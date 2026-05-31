from __future__ import annotations

import time


class CMEngineError(RuntimeError):
    """Raised when OMICRON CMEngine cannot complete an operation."""


class CMEngine:
    """Small wrapper around OMICRON CMEngine COM commands."""

    def __init__(self, log_callback=None):
        self.log = log_callback or print
        self.device_id: int | None = None
        self.device_info: dict = {}
        self.device_locked = False
        self.cm_engine = None
        self._pythoncom = None
        self._co_initialized = False

    def _ensure_com(self):
        if self.cm_engine is not None:
            return
        try:
            import pythoncom
            import win32com.client
        except Exception as e:
            raise CMEngineError(
                "pywin32/CMEngine dependency is not available. "
                "Install OMICRON software and pywin32."
            ) from e

        try:
            pythoncom.CoInitialize()
            self._pythoncom = pythoncom
            self._co_initialized = True
            self.cm_engine = win32com.client.Dispatch("OMICRON.CMEngAL")
        except Exception as e:
            self.cm_engine = None
            raise CMEngineError(
                "Failed to create OMICRON.CMEngAL COM object."
            ) from e

    @staticmethod
    def _parse_device_list(raw: str) -> list[list[str]]:
        return [item.split(",") for item in str(raw or "").split(";") if item]

    def connect(self) -> dict:
        if self.device_locked:
            return self.refresh()

        self._ensure_com()
        self.log("[cmc] scanning devices")
        self.cm_engine.DevScanForNew(False)
        devices = self._parse_device_list(self.cm_engine.DevGetList(0))
        if not devices:
            raise CMEngineError("No CMC device found.")

        try:
            self.device_id = int(devices[0][0])
            self.cm_engine.DevLock(self.device_id)
            self.device_locked = True
            self.device_info = self._read_device_info()
        except Exception as e:
            self.device_locked = False
            raise CMEngineError("Failed to lock CMC device.") from e

        self.log(
            "[cmc] locked "
            f"{self.device_info.get('serial', '')} "
            f"{self.device_info.get('ip', '')}".strip()
        )
        return self.device_info

    def refresh(self) -> dict:
        if self.cm_engine is None or self.device_id is None:
            return self.connect()
        try:
            self.device_info = self._read_device_info()
            self.query("seq:status?(step)")
        except Exception as e:
            self.log(f"[cmc] refresh failed: {e}")
            self.release()
            return self.connect()
        return self.device_info

    def _read_device_info(self) -> dict:
        if self.cm_engine is None or self.device_id is None:
            raise CMEngineError("CMC is not connected.")
        serial = ""
        ip = ""
        try:
            serial = str(self.cm_engine.SerialNumber(self.device_id))
        except Exception:
            pass
        try:
            ip = str(self.cm_engine.IPAddress(self.device_id))
        except Exception:
            pass
        return {
            "device_id": self.device_id,
            "serial": serial,
            "ip": ip,
            "locked": self.device_locked,
        }

    def release(self):
        try:
            if self.cm_engine is not None and self.device_locked and self.device_id is not None:
                try:
                    self.out_off()
                except Exception:
                    pass
                self.cm_engine.DevUnlock(self.device_id)
                self.log("[cmc] device unlocked")
        finally:
            self.device_locked = False
            self.device_id = None
            self.device_info = {}
            self.cm_engine = None
            if self._co_initialized and self._pythoncom is not None:
                try:
                    self._pythoncom.CoUninitialize()
                except Exception:
                    pass
            self._co_initialized = False
            self._pythoncom = None

    def execute(self, command: str):
        if self.cm_engine is None or self.device_id is None:
            raise CMEngineError("CMC is not connected.")
        return self.cm_engine.Exec(self.device_id, command)

    def query(self, command: str):
        return self.execute(command)

    def out_off(self):
        if self.cm_engine is not None and self.device_id is not None:
            self.execute("out:off")

    def apply_output(self, step: dict):
        """Apply one output state and keep it on until out_off() is called."""
        self.connect()
        self._write_step_outputs(step)
        self.execute("out:on")

    def run_sequence(self, steps: list[dict], stop_event=None):
        if not steps:
            raise CMEngineError("Sequence is empty.")
        if stop_event is not None and stop_event.is_set():
            return

        self.connect()
        self.execute("seq:clr")
        self.execute("seq:begin")

        total_seconds = 0.0
        for index, step in enumerate(steps, 1):
            if stop_event is not None and stop_event.is_set():
                break
            self.log(f"[cmc] step {index}: {step.get('name') or index}")
            self._write_step_outputs(step)
            self.execute("out:on")
            duration = float(step.get("duration", 0))
            total_seconds += max(0.0, duration)
            self.execute(f"seq:wait({duration}, 1)")

        self.execute("out:off")
        self.execute("seq:end")
        if stop_event is not None and stop_event.is_set():
            self.out_off()
            return
        self.log("[cmc] executing sequence")
        self.execute("seq:exec")
        self._wait_for_sequence(total_seconds + 30, stop_event)

    def _write_step_outputs(self, step: dict):
        freq = float(step.get("frequency", 60))
        voltages = [
            float(step.get("va", 0)),
            float(step.get("vb", 0)),
            float(step.get("vc", 0)),
        ]
        currents = [
            float(step.get("ia", 0)),
            float(step.get("ib", 0)),
            float(step.get("ic", 0)),
        ]
        phases = step.get("phases") or {}
        voltage_phases = phases.get("voltage") or [0, 240, 120]
        current_phases = phases.get("current") or [0, 240, 120]

        for channel, value in enumerate(voltages, 1):
            phase = float(voltage_phases[channel - 1])
            self.execute(f"out:v(1:{channel}):a({value});p({phase});f({freq})")
        for channel, value in enumerate(currents, 1):
            phase = float(current_phases[channel - 1])
            self.execute(f"out:i(1:{channel}):a({value});p({phase});f({freq})")

    def _wait_for_sequence(self, timeout_seconds: float, stop_event=None):
        started = time.time()
        last_step = None
        while True:
            if stop_event is not None and stop_event.is_set():
                try:
                    self.execute("seq:stop")
                except Exception:
                    pass
                self.out_off()
                return
            if timeout_seconds and time.time() - started > timeout_seconds:
                self.out_off()
                raise CMEngineError("Sequence did not finish before timeout.")
            response = self.query("seq:status?(step)")
            try:
                step = int(str(response).split(",")[1].strip().strip(";"))
            except Exception:
                step = None
            if step != last_step:
                self.log(f"[cmc] sequence step = {step}")
                last_step = step
            if step == 0:
                self.log("[cmc] sequence finished")
                return
            time.sleep(0.5)
