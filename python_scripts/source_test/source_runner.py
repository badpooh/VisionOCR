from __future__ import annotations

import csv
import os
import re
import shutil
import struct
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

    def __init__(self, log_callback=None, case_status_callback=None):
        self.log = log_callback or print
        self.case_status_callback = case_status_callback
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
                self._report_case_status(idx - 1, case, "RUNNING")
                try:
                    case_rows = self._run_case(case, save_dir)
                except Exception as exc:
                    self._report_case_status(
                        idx - 1, case, "ERROR", str(exc)
                    )
                    raise

                rows.extend(case_rows)
                if self.stop_event.is_set():
                    self._report_case_status(
                        idx - 1, case, "ERROR", "Stopped by user"
                    )
                    break

                self._report_case_status(
                    idx - 1,
                    case,
                    _overall(case_rows),
                    _first_failure_summary(case_rows),
                )
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

    def _report_case_status(
        self, index: int, case: dict, status: str, failure_summary: str = ""
    ):
        if self.case_status_callback is None:
            return
        self.case_status_callback({
            "index": index,
            "tc_id": case.get("tc_id", ""),
            "status": status,
            "failure_summary": failure_summary,
        })

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

            rows.extend(self._read_measurement_modbus(case, output))
            self._navigate(case.get("navigation") or [])
            image_path, ocr_with_boxes = self._capture_ocr(case, output, save_dir)
            expected = [
                item for item in (case.get("expected") or [])
                if not item.get("source_name") or item.get("source_name") == source_name
            ]
            fixed_result = self._evaluate_fixed_text(
                case, output, expected, image_path, ocr_with_boxes
            )
            if fixed_result is not None:
                rows.append(fixed_result)
            for check in expected:
                if check.get("expected") is None:
                    continue
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

    def _read_measurement_modbus(self, case: dict, output: dict) -> list[dict]:
        source_name = output.get("name", "")
        checks = [
            item for item in (case.get("measurement_modbus") or [])
            if not item.get("source_name") or item.get("source_name") == source_name
        ]
        rows = []
        for check in checks:
            if self.stop_event.is_set():
                break
            rows.append(self._read_measurement_check(case, output, check))
        return rows

    def _read_measurement_check(self, case, output, check) -> dict:
        client = self.connect_manager.setup_client
        doc_address = check.get("doc_address")
        address = check.get("address")
        value_type = check.get("value_type") or "float"
        expected = check.get("expected")
        actual = None
        error = None
        limit = None
        overall = "ERROR"

        try:
            if client is None:
                raise RuntimeError("setup_client is not connected")
            if address is None:
                raise ValueError("Address is required")
            if expected is None:
                raise ValueError("Expected is required")

            word_count = _type_words(value_type)
            self.log(
                f"[measurement_modbus] {check.get('check_name')} "
                f"doc_addr={doc_address} type={value_type}"
            )
            response = client.read_holding_registers(address, count=word_count)
            if response is None or (
                hasattr(response, "isError") and response.isError()
            ):
                raise RuntimeError(f"read failed: {response}")

            registers = list(getattr(response, "registers", []) or [])
            if len(registers) < word_count:
                raise RuntimeError(
                    f"read short: {len(registers)} < {word_count}"
                )

            actual = _decode_register_value(registers, value_type)
            error = float(actual) - float(expected)
            limit = _percent_limit(float(expected), check.get("tolerance"))
            overall = "PASS" if abs(error) <= limit else "FAIL"
        except Exception as exc:
            error = str(exc)
            self.log(
                f"[measurement_modbus] {check.get('check_name')} failed: {exc}"
            )

        return {
            "tc_id": case.get("tc_id"),
            "test_name": case.get("name"),
            "source_name": output.get("name"),
            "check_name": check.get("check_name"),
            "expected": expected,
            "actual": actual,
            "unit": check.get("unit") or "",
            "tolerance": check.get("tolerance"),
            "tolerance_type": "percent",
            "error": error,
            "limit": limit,
            "label_ok": True,
            "unit_ok": True,
            "overall": overall,
            "ocr_text": f"Modbus document address {doc_address}",
            "image_path": "",
        }

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
            for keyin in action.get("button_keyin") or []:
                self.touch_manager.button(int(keyin))
                time.sleep(0.3)
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

    def _evaluate_fixed_text(self, case, output, expected, image_path, ocr_with_boxes):
        required_texts = [
            item.get("required_text")
            for item in expected
            if item.get("required_text")
        ]
        if not required_texts:
            return None

        units = {
            str(item.get("unit")).strip()
            for item in expected
            if item.get("unit") is not None and str(item.get("unit")).strip()
        }
        ocr_tokens = [text for text, _box in ocr_with_boxes if text]
        fixed_tokens = _fixed_text_tokens(ocr_tokens, units)
        missing, extra = _compare_fixed_texts(fixed_tokens, required_texts)
        ok = not missing and not extra
        details = list(missing) + [f"[unexpected] {item}" for item in extra]

        return {
            "tc_id": case.get("tc_id"),
            "test_name": case.get("name"),
            "source_name": output.get("name"),
            "check_name": "Fixed Text",
            "expected": " | ".join(str(item) for item in required_texts),
            "actual": "",
            "unit": "",
            "tolerance": "",
            "tolerance_type": "",
            "error": "; ".join(details),
            "limit": "",
            "label_ok": ok,
            "unit_ok": True,
            "overall": "PASS" if ok else "FAIL",
            "ocr_text": " | ".join(fixed_tokens),
            "image_path": image_path,
        }

    def _evaluate(self, case, output, check, image_path, ocr_with_boxes) -> dict:
        roi = check.get("roi_xy")
        required = check.get("required_text") or ""
        tokens = _select_ocr_tokens(ocr_with_boxes, required, roi)
        joined = " ".join(tokens)
        label_ok = (not required) or _contains_required(joined, required)

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
                limit = _percent_limit(float(expected), check.get("tolerance"))
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
            "tolerance_type": "percent",
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
    return 2 if (value_type or "").lower() in (
        "uint32", "int32", "float", "float32"
    ) else 1


def _decode_register_value(registers: list[int], value_type: str):
    kind = (value_type or "uint16").lower()
    words = [int(value) & 0xFFFF for value in registers]

    if kind == "uint16":
        return words[0]
    if kind == "int16":
        return words[0] - 0x10000 if words[0] & 0x8000 else words[0]
    if kind == "uint32":
        return (words[0] << 16) | words[1]
    if kind == "int32":
        value = (words[0] << 16) | words[1]
        return value - 0x100000000 if value & 0x80000000 else value
    if kind in ("float", "float32"):
        return struct.unpack(">f", struct.pack(">HH", words[0], words[1]))[0]
    raise ValueError(f"unsupported value_type: {value_type}")


def _inside_roi(box, roi) -> bool:
    if roi is None:
        return True
    cx = (box[0] + box[2]) / 2
    cy = (box[1] + box[3]) / 2
    return roi[0] <= cx <= roi[2] and roi[1] <= cy <= roi[3]


def _fixed_text_tokens(ocr_tokens: list[str], units: set[str]) -> list[str]:
    out = []
    for token in ocr_tokens:
        text = str(token).strip()
        if not text:
            continue
        if _is_number_token(text):
            continue
        if _looks_like_timestamp(text):
            continue
        if text in units:
            continue
        out.append(text)
    return out


def _compare_fixed_texts(ocr_tokens: list[str], required_texts: list[str]):
    used = set()
    missing = []

    for expected in required_texts:
        match_idx = None
        for idx, token in enumerate(ocr_tokens):
            if idx in used:
                continue
            if _contains_required(token, str(expected)):
                match_idx = idx
                break
        if match_idx is None:
            missing.append(str(expected))
        else:
            used.add(match_idx)

    extra = []
    for idx, token in enumerate(ocr_tokens):
        if idx not in used:
            extra.append(f"{token} x1")
    return missing, extra


def _looks_like_timestamp(text: str) -> bool:
    value = str(text or "")
    return bool(
        re.search(r"\d{4}[-/.]\d{1,2}[-/.]\d{1,2}", value)
        or re.search(r"\d{1,2}:\d{2}(?::\d{2})?", value)
    )


def _is_number_token(text: str) -> bool:
    return bool(re.fullmatch(r"[-+]?\d+(?:\.\d+)?", str(text or "").strip()))


def _select_ocr_tokens(ocr_with_boxes, required: str, roi):
    if required:
        row_tokens = _tokens_on_required_row(ocr_with_boxes, required)
        if row_tokens:
            return row_tokens

    if roi is not None:
        return [
            text for text, box in ocr_with_boxes
            if text and _inside_roi(box, roi)
        ]

    return [text for text, _box in ocr_with_boxes if text]


def _tokens_on_required_row(ocr_with_boxes, required: str) -> list[str]:
    anchors = []
    for text, box in ocr_with_boxes:
        if text and _contains_required(text, required):
            anchors.append((text, box))
    if not anchors:
        return []

    anchor_text, anchor_box = anchors[0]
    ay = _box_center_y(anchor_box)
    ax1 = min(anchor_box[0], anchor_box[2])
    anchor_h = abs(anchor_box[3] - anchor_box[1])
    row_tol = max(24.0, anchor_h * 1.4)

    row = []
    for text, box in ocr_with_boxes:
        if not text:
            continue
        cy = _box_center_y(box)
        cx = _box_center_x(box)
        if abs(cy - ay) <= row_tol and cx >= ax1 - 16:
            row.append((cx, text))
    row.sort(key=lambda item: item[0])

    tokens = [text for _cx, text in row]
    if anchor_text not in tokens:
        tokens.insert(0, anchor_text)
    return tokens


def _box_center_x(box) -> float:
    return (float(box[0]) + float(box[2])) / 2


def _box_center_y(box) -> float:
    return (float(box[1]) + float(box[3])) / 2


def _contains_required(text: str, required: str) -> bool:
    haystack = _normalize_required_text(text)
    words = None
    for candidate in _required_candidates(required):
        if candidate.isascii() and candidate.isalnum() and len(candidate) <= 3:
            if words is None:
                words = {
                    _normalize_required_text(word)
                    for word in re.findall(r"[0-9A-Za-z]+", str(text or ""))
                }
            if candidate in words:
                return True
        elif candidate in haystack:
            return True
    return False


def _required_candidates(required: str) -> list[str]:
    value = _normalize_required_text(required)
    candidates = [value] if value else []
    if value.startswith("v") and len(value) > 1:
        candidates.append(value[1:])
    return candidates


def _normalize_required_text(text: str) -> str:
    return re.sub(r"[^0-9A-Za-z가-힣]+", "", str(text or "")).lower()


def _first_number(text: str):
    match = re.search(r"[-+]?\d+(?:\.\d+)?", text or "")
    return float(match.group(0)) if match else None


def _percent_limit(expected: float, tolerance):
    tol = float(tolerance or 0)
    return abs(expected) * tol / 100


def _overall(rows: list[dict]) -> str:
    if not rows:
        return "PASS"
    statuses = {row.get("overall") for row in rows}
    if "ERROR" in statuses:
        return "ERROR"
    return "FAIL" if "FAIL" in statuses else "PASS"


def _first_failure_summary(rows: list[dict]) -> str:
    for row in rows:
        status = row.get("overall")
        if status not in ("FAIL", "ERROR"):
            continue

        check_name = str(row.get("check_name") or "Check")
        error = row.get("error")
        expected = row.get("expected")
        actual = row.get("actual")

        if status == "ERROR" and error not in (None, ""):
            detail = str(error).split(";", 1)[0].strip()
        elif check_name == "Fixed Text" and error not in (None, ""):
            detail = str(error).split(";", 1)[0].strip()
        elif row.get("label_ok") is False:
            detail = "required text not found"
        elif row.get("unit_ok") is False:
            detail = f"unit {row.get('unit') or ''} not found".strip()
        elif expected is not None:
            actual_text = "not found" if actual is None else str(actual)
            detail = f"expected {expected}, actual {actual_text}"
        elif error not in (None, ""):
            detail = str(error).split(";", 1)[0].strip()
        else:
            detail = status
        return f"{check_name}: {detail}"
    return ""
