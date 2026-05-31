from __future__ import annotations

import csv
import os
import re
import shutil
import threading
import time
from datetime import datetime

from demo_test.demo_process import get_image_directory
from external.cmengine import CMEngine
from function.func_connection import ConnectionManager
from function.func_evaluation import Evaluation
from function.func_ocr import PaddleOCRManager, YoloManager
from function.func_touch import TouchManager


class SourceTestRunner:
    """Runs CMC-driven display function tests."""

    def __init__(self, log_callback=None):
        self.log = log_callback or print
        self.stop_event = threading.Event()
        self.cmc = CMEngine(log_callback=self.log)
        self.connect_manager = ConnectionManager()
        self.touch_manager = TouchManager()
        self.eval_manager = Evaluation()
        self.yolo = YoloManager()
        self.paddleocr = PaddleOCRManager()

    def cancel(self):
        self.stop_event.set()
        try:
            self.cmc.out_off()
        except Exception:
            pass

    def run(self, cases: list[dict], save_dir: str) -> dict:
        os.makedirs(save_dir, exist_ok=True)
        started = datetime.now()
        rows = []
        result = {
            "started": started.isoformat(timespec="seconds"),
            "finished": "",
            "overall": "RUNNING",
            "cases": len(cases),
            "error": "",
            "save_dir": save_dir,
        }
        try:
            for idx, case in enumerate(cases, 1):
                if self.stop_event.is_set():
                    break
                self.log(f"[test] ({idx}/{len(cases)}) {case['tc_id']} {case['name']}")
                rows.extend(self._run_case(case, save_dir))
            result["overall"] = "STOPPED" if self.stop_event.is_set() else _overall(rows)
        except Exception as e:
            result["overall"] = "ERROR"
            result["error"] = str(e)
            self.log(f"[functional test] error: {e}")
            try:
                self.cmc.out_off()
            except Exception:
                pass
        finally:
            result["finished"] = datetime.now().isoformat(timespec="seconds")
            self._save_summary(save_dir, rows, result)
            self.cmc.release()
        return result

    def _run_case(self, case: dict, save_dir: str) -> list[dict]:
        rows = []
        self._apply_setup_modbus(case.get("setup_modbus") or [])

        outputs = case.get("cmc_outputs") or []
        if not outputs:
            outputs = [{"name": "No CMC Output", "duration": 0}]

        for output in outputs:
            if self.stop_event.is_set():
                break
            source_name = output.get("name", "")
            if output.get("duration", 0) or any(output.get(k, 0) for k in ("va", "vb", "vc", "ia", "ib", "ic")):
                self.log(f"[cmc] apply output: {source_name}")
                self.cmc.apply_output(output)

            settle_s = max(float(case.get("settle_s") or 0), float(output.get("duration") or 0))
            self._wait(settle_s)

            self._navigate(case.get("navigation") or [])
            image_path, ocr_with_boxes = self._capture_ocr(case, output, save_dir)
            expected = [
                item for item in (case.get("expected") or [])
                if not item.get("source_name") or item.get("source_name") == source_name
            ]
            for check in expected:
                rows.append(self._evaluate(case, output, check, image_path, ocr_with_boxes))

        try:
            self.cmc.out_off()
        except Exception:
            pass
        return rows

    def _apply_setup_modbus(self, settings: list[dict]):
        if not settings:
            return
        client = self.connect_manager.setup_client
        if client is None:
            raise RuntimeError("setup_client is not connected; cannot apply setup_modbus.")
        self._unlock_setup()
        for item in settings:
            if self.stop_event.is_set():
                return
            addr = item.get("address")
            value = item.get("write_value")
            if addr is None or value is None:
                self.log(f"[setup_modbus] skip invalid setting: {item.get('name')}")
                continue
            self.log(
                f"[setup_modbus] {item.get('name')} "
                f"doc_addr={item.get('doc_address')} write={value}"
            )
            self._write_setting(item)
            time.sleep(0.15)

    def _unlock_setup(self):
        client = self.connect_manager.setup_client
        if client is None:
            return
        product = self.connect_manager.PRODUCT or "A7300"
        if product == "A2700":
            for addr, values in (
                (50999, [2300, 0, 700, 1]),
                (54999, [2300, 0, 1600, 1]),
            ):
                for value in values:
                    client.write_register(addr, value)
                    time.sleep(0.25)
            return

        for value in [2300, 0, 1600, 1]:
            client.write_register(54999, value)
            time.sleep(0.25)

    def _write_setting(self, item: dict):
        client = self.connect_manager.setup_client
        access_addr = item.get("access_address")
        target_addr = item.get("address")
        value_type = item.get("value_type") or "uint16"
        value = item.get("write_value")
        access_value = item.get("access_value", 1)

        if access_addr is not None:
            count = max(1, (target_addr + _type_words(value_type)) - access_addr)
            if target_addr >= access_addr:
                try:
                    client.read_holding_registers(access_addr, count=count)
                    time.sleep(0.1)
                except Exception:
                    pass

        words = self._encode_value(value, value_type, client)
        for offset, word in enumerate(words):
            client.write_register(target_addr + offset, int(word) & 0xFFFF)
            time.sleep(0.03)

        if access_addr is not None:
            client.write_register(access_addr, int(access_value) & 0xFFFF)

    @staticmethod
    def _encode_value(value, value_type: str, client) -> list[int]:
        t = (value_type or "uint16").lower()
        if t == "uint16":
            return [int(value) & 0xFFFF]
        if t == "int16":
            return [int(value) & 0xFFFF]
        if t == "uint32":
            v = int(value) & 0xFFFFFFFF
            return [(v >> 16) & 0xFFFF, v & 0xFFFF]
        if t == "int32":
            v = int(value) & 0xFFFFFFFF
            return [(v >> 16) & 0xFFFF, v & 0xFFFF]
        if t == "float":
            return client.convert_to_registers(
                float(value), client.DATATYPE.FLOAT32, word_order="big"
            )
        raise ValueError(f"unsupported value_type: {value_type}")

    def _navigate(self, actions: list[dict]):
        for action in actions:
            if self.stop_event.is_set():
                return
            self.log(f"[nav] {action.get('name')}")
            for key in ("main_menu_xy", "side_menu_xy", "data_view_xy"):
                for xy in action.get(key) or []:
                    self.touch_manager.touch_menu(list(xy))
                    time.sleep(0.3)
            self._wait(float(action.get("wait_s") or 0))

    def _capture_ocr(self, case: dict, output: dict, save_dir: str):
        start_time = datetime.now()
        self.touch_manager.screenshot()
        search_pattern = os.path.join(get_image_directory(), "**", "*.png")
        image_path = self.eval_manager.load_image_file(search_pattern, start_time)
        saved_path = image_path
        if image_path:
            try:
                name = f"{case['tc_id']}_{output.get('name', 'output')}".replace(" ", "_")
                dst = os.path.join(save_dir, f"{name}_{os.path.basename(image_path)}")
                shutil.copy(image_path, dst)
                saved_path = dst
            except Exception as e:
                self.log(f"[capture] copy failed: {e}")

        ocr_with_boxes = []
        if image_path:
            try:
                cropped, _names, boxes = self.yolo.yolo_basic(image_path, return_boxes=True)
                ocr_with_boxes = self.paddleocr.paddleocr_basic(image=cropped, boxes=boxes)
            except Exception as e:
                self.log(f"[ocr] failed: {e}")
        return saved_path, ocr_with_boxes

    def _evaluate(self, case, output, check, image_path, ocr_with_boxes) -> dict:
        roi = check.get("roi_xy")
        tokens = [text for text, box in ocr_with_boxes if text and _inside_roi(box, roi)]
        joined = " ".join(tokens)
        required = check.get("required_text") or ""
        label_ok = (not required) or (required in joined)

        actual = _first_number(joined)
        expected = check.get("expected")
        numeric_ok = True
        error = None
        limit = None
        if expected is not None:
            if actual is None:
                numeric_ok = False
            else:
                error = actual - float(expected)
                limit = _limit(float(expected), check.get("tolerance"), check.get("tolerance_type"))
                numeric_ok = abs(error) <= limit

        unit = check.get("unit") or ""
        unit_ok = (not unit) or (unit in joined)
        overall = "PASS" if label_ok and numeric_ok and unit_ok else "FAIL"
        return {
            "tc_id": case.get("tc_id"),
            "test_name": case.get("name"),
            "source_name": output.get("name"),
            "check_name": check.get("check_name"),
            "expected": expected,
            "actual": actual,
            "unit": unit,
            "tolerance": check.get("tolerance"),
            "tolerance_type": check.get("tolerance_type"),
            "error": error,
            "limit": limit,
            "label_ok": label_ok,
            "unit_ok": unit_ok,
            "overall": overall,
            "ocr_text": joined,
            "image_path": image_path,
        }

    def _wait(self, seconds: float):
        end = time.time() + max(0.0, seconds)
        while time.time() < end:
            if self.stop_event.is_set():
                return
            time.sleep(min(0.2, end - time.time()))

    def _save_summary(self, save_dir: str, rows: list[dict], result: dict):
        path = os.path.join(save_dir, "0.functional_test_summary.csv")
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["started", result.get("started", "")])
            writer.writerow(["finished", result.get("finished", "")])
            writer.writerow(["overall", result.get("overall", "")])
            writer.writerow(["error", result.get("error", "")])
            writer.writerow([])
            writer.writerow([
                "TC_ID", "Test Name", "Source Name", "Check Name", "Overall",
                "Expected", "Actual", "Unit", "Tolerance Type", "Tolerance",
                "Error", "Limit", "Label OK", "Unit OK", "OCR Text", "Image Path",
            ])
            for row in rows:
                writer.writerow([
                    row.get("tc_id", ""),
                    row.get("test_name", ""),
                    row.get("source_name", ""),
                    row.get("check_name", ""),
                    row.get("overall", ""),
                    row.get("expected", ""),
                    row.get("actual", ""),
                    row.get("unit", ""),
                    row.get("tolerance_type", ""),
                    row.get("tolerance", ""),
                    row.get("error", ""),
                    row.get("limit", ""),
                    row.get("label_ok", ""),
                    row.get("unit_ok", ""),
                    row.get("ocr_text", ""),
                    row.get("image_path", ""),
                ])
        self.log(f"[save] summary csv -> {path}")


def _type_words(value_type: str) -> int:
    return 2 if (value_type or "").lower() in ("uint32", "int32", "float") else 1


def _inside_roi(box, roi) -> bool:
    if roi is None:
        return True
    cx = (box[0] + box[2]) / 2
    cy = (box[1] + box[3]) / 2
    return roi[0] <= cx <= roi[2] and roi[1] <= cy <= roi[3]


def _first_number(text: str):
    match = re.search(r"[-+]?\d+(?:\.\d+)?", text or "")
    return float(match.group(0)) if match else None


def _limit(expected: float, tolerance, tolerance_type: str | None):
    tol = float(tolerance or 0)
    if (tolerance_type or "").lower().startswith("percent"):
        return abs(expected) * tol / 100
    return tol


def _overall(rows: list[dict]) -> str:
    if not rows:
        return "PASS"
    return "PASS" if all(row.get("overall") == "PASS" for row in rows) else "FAIL"
