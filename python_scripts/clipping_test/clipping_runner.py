# -*- coding: utf-8 -*-
"""Modbus-only clipping test runner."""

from __future__ import annotations

import time
import traceback

from function.func_connection import ConnectionManager


FLOAT_TOLERANCE = 1e-3


class ClippingRunner:
    def __init__(self, log_callback=None):
        self.connect_manager = ConnectionManager()
        self.log = log_callback or print
        self.stop_requested = False

    def cancel(self):
        self.stop_requested = True

    def run(self, cases: list[dict], product: str = "A2700", result_callback=None) -> list[dict]:
        results = []
        self.log(f"[clipping] {len(cases)} case(s) ready for {product}")
        if cases and self.connect_manager.setup_client is not None:
            try:
                self._unlock_setup(product)
                self.log("[clipping] setup unlocked")
            except Exception as exc:
                self.log(
                    f"[clipping] initial unlock failed: {exc}; "
                    "write/read steps will retry unlock if needed"
                )
        for i, case in enumerate(cases, 1):
            if self.stop_requested:
                self.log("[clipping] canceled")
                break
            try:
                self.log(f"[clipping] ({i}/{len(cases)}) {case['name']}")
                res = self._run_one(case, product)
            except Exception as exc:
                traceback.print_exc()
                res = {
                    "name": case.get("name", ""),
                    "overall": "ERROR",
                    "error": str(exc),
                }
            res["index"] = i
            results.append(res)
            self.log(f"  -> {res.get('overall')}")
            if result_callback is not None:
                try:
                    result_callback(res)
                except Exception as exc:
                    self.log(f"[clipping] result_callback failed: {exc}")
        return results

    def _run_one(self, case: dict, product: str) -> dict:
        client = self.connect_manager.setup_client
        if client is None:
            return {
                "name": case["name"],
                "overall": "ERROR",
                "error": "setup_client is not connected",
            }

        case_product = str(case.get("product") or "").strip()
        if case_product and case_product.upper() != str(product).upper():
            return {
                "name": case["name"],
                "overall": "SKIP",
                "note": f"product mismatch: case={case_product}, current={product}",
            }

        if case.get("write_value") is None:
            return {
                "name": case["name"],
                "overall": "ERROR",
                "error": "write_value is empty",
            }

        restored = None
        restore_error = None
        try:
            actual = self._with_unlock_retry(
                product,
                "write/read",
                lambda: self._write_read_case(case, case["write_value"], "write"),
            )
            expected_ok = self._expected_ok(actual, case)
            range_ok = self._range_ok(actual, case)
            if not (expected_ok and range_ok):
                self.log(
                    "[clipping] readback mismatch; unlock and retry write once"
                )
                self._unlock_setup(product)
                actual = self._write_read_case(case, case["write_value"], "write retry")
                expected_ok = self._expected_ok(actual, case)
                range_ok = self._range_ok(actual, case)
            overall = "PASS" if expected_ok and range_ok else "FAIL"
            note_parts = []
            if case.get("notes"):
                note_parts.append(str(case["notes"]))
            if case.get("expected_value") is None:
                note_parts.append("expected_value blank: range only")
            if not expected_ok:
                note_parts.append(f"expected {case.get('expected_value')!r}, got {actual!r}")
            if not range_ok:
                note_parts.append(
                    f"out of range {case.get('valid_low')!r}~{case.get('valid_high')!r}"
                )
        finally:
            if case.get("restore_after") and case.get("restore_value") is not None:
                try:
                    restored = self._with_unlock_retry(
                        product,
                        "restore write/read",
                        lambda: self._write_read_case(
                            case, case["restore_value"], "restore"
                        ),
                    )
                    if not self._same_value(
                        restored, case["restore_value"], case.get("read_value_type")
                    ):
                        self.log(
                            "[clipping] restore readback mismatch; "
                            "unlock and retry restore once"
                        )
                        self._unlock_setup(product)
                        restored = self._write_read_case(
                            case, case["restore_value"], "restore retry"
                        )
                    if not self._same_value(
                        restored, case["restore_value"], case.get("read_value_type")
                    ):
                        raise RuntimeError(
                            f"restore readback {restored!r} != "
                            f"{case['restore_value']!r}"
                        )
                    self.log(f"[clipping] restore readback -> {restored!r}")
                except Exception as exc:
                    restore_error = str(exc)

        if restore_error:
            overall = "ERROR"
            note_parts.append(f"restore failed: {restore_error}")

        return {
            "name": case["name"],
            "overall": overall,
            "command": (
                f"Modbus[{case['addr_doc']}]={case['write_value']!r} "
                f"({case['value_type']})"
            ),
            "readback": (
                f"Modbus[{case['read_doc_addr']}]={actual!r} "
                f"expected={case.get('expected_value')!r}"
            ),
            "actual_value": actual,
            "expected_ok": expected_ok,
            "range_ok": range_ok,
            "restored_value": restored,
            "note": " | ".join(note_parts),
        }

    def _write_read_case(self, case: dict, value, label: str):
        self._write_and_commit(case, value, label)
        time.sleep(max(0, int(case.get("settle_ms") or 0)) / 1000.0)
        return self._read_case_value(case)

    def _with_unlock_retry(self, product: str, label: str, action):
        try:
            return action()
        except Exception as exc:
            self.log(
                f"[clipping] {label} failed: {exc}; "
                "unlock and retry once"
            )
            self._unlock_setup(product)
            return action()

    def _unlock_setup(self, product: str) -> bool:
        """(공용 로직: function/modbus_unlock.py — 스펙은 제품 config 모듈)"""
        from function.modbus_unlock import unlock_setup
        client = self.connect_manager.setup_client
        if client is None:
            raise RuntimeError("setup_client is not connected")
        if not unlock_setup(client, product, log=self.log):
            # 기존 semantics 유지: 언락 실패는 예외로 케이스 중단
            raise RuntimeError(f"setup unlock failed ({product})")
        return True

    def _write_and_commit(self, case: dict, value, label: str):
        access_addr = case.get("access_addr")
        target_addr = case["addr"]
        words = int(case.get("words") or 1)

        if access_addr is not None:
            count = max(1, (target_addr + words) - access_addr)
            self.log(
                f"[clipping] {label}: preload access doc={case['access_doc_addr']} "
                f"addr={access_addr} count={count}"
            )
            self._read_registers(access_addr, count)
            time.sleep(0.2)

        encoded = self._encode_value(value, case.get("value_type"))
        for offset, word in enumerate(encoded):
            self._write_single(target_addr + offset, word, label)
            time.sleep(0.05)

        if access_addr is not None:
            commit_value = case.get("commit_value")
            if commit_value is None:
                commit_value = 1
            self._write_single(access_addr, commit_value, f"{label} commit")
            self.log(
                f"[clipping] {label}: commit access doc={case['access_doc_addr']} "
                f"value={commit_value!r}"
            )
            time.sleep(0.5)

    def _read_case_value(self, case: dict):
        access_addr = case.get("access_addr")
        read_addr = case["read_addr"]
        read_words = int(case.get("read_words") or 1)
        if access_addr is not None:
            count = max(1, (read_addr + read_words) - access_addr)
            self._read_registers(access_addr, count)
            time.sleep(0.2)
        regs = self._read_registers(read_addr, read_words)
        return self._decode_value(regs, case.get("read_value_type"))

    def _read_registers(self, addr: int, count: int) -> list[int]:
        client = self.connect_manager.setup_client
        resp = client.read_holding_registers(addr, count=count)
        if resp is None or (hasattr(resp, "isError") and resp.isError()):
            raise RuntimeError(f"read failed addr={addr} count={count}: {resp}")
        return list(resp.registers)

    def _write_single(self, addr: int, value, label: str):
        client = self.connect_manager.setup_client
        word = int(value) & 0xFFFF
        self.log(f"[clipping] {label}: FC6 write addr={addr} value={word}")
        resp = client.write_register(addr, word)
        if resp is None or (hasattr(resp, "isError") and resp.isError()):
            raise RuntimeError(f"write failed addr={addr} value={word}: {resp}")

    def _encode_value(self, value, value_type: str) -> list[int]:
        """(공용 로직: function/modbus_values.py — setup runner 와 공유)"""
        from function.modbus_values import encode_value
        client = self.connect_manager.setup_client
        return encode_value(value, value_type, client)

    def _decode_value(self, regs: list[int], value_type: str):
        """(공용 로직: function/modbus_values.py — setup runner 와 공유)"""
        from function.modbus_values import decode_registers
        client = self.connect_manager.setup_client
        return decode_registers(regs, value_type, client)

    def _expected_ok(self, actual, case: dict) -> bool:
        expected = case.get("expected_value")
        if expected is None:
            return True
        value_type = (case.get("read_value_type") or "").lower()
        if value_type == "float":
            return abs(float(actual) - float(expected)) <= FLOAT_TOLERANCE
        return actual == expected

    @staticmethod
    def _same_value(actual, expected, value_type: str) -> bool:
        if expected is None:
            return True
        if actual is None:
            return False
        if (value_type or "").lower() == "float":
            return abs(float(actual) - float(expected)) <= FLOAT_TOLERANCE
        return actual == expected

    @staticmethod
    def _range_ok(actual, case: dict) -> bool:
        if actual is None:
            return False
        low = case.get("valid_low")
        high = case.get("valid_high")
        if low is not None and float(actual) < float(low):
            return False
        if high is not None and float(actual) > float(high):
            return False
        return True
