from __future__ import annotations

import csv
import os
import shutil
import struct
import threading
import time
import traceback
from datetime import datetime

from demo_test.demo_process import get_image_directory
from external.cmengine import CMEngine
from function import ocr_eval_helpers as ocr_eval
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
            self._prepare_setup_connection(cases)
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
            traceback.print_exc()  # 스택 추적 보존 (디버깅용)
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
            image_path, ocr_with_boxes, ocr_error = self._capture_ocr(
                case, output, save_dir
            )
            expected = [
                item for item in (case.get("expected") or [])
                if not item.get("source_name") or item.get("source_name") == source_name
            ]
            # OCR 기반 검증이 필요한데 스크린샷/OCR 단계 자체가 실패했으면
            # 빈 토큰으로 비교(오판 위험)하지 않고 명시적 ERROR row 로 남긴다.
            needs_ocr = any(
                item.get("required_text") or item.get("expected") is not None
                for item in expected
            )
            if ocr_error and needs_ocr:
                self.log(f"[test] OCR phase failed — mark ERROR: {ocr_error}")
                rows.append({
                    "tc_id": case.get("tc_id"),
                    "test_name": case.get("name"),
                    "source_name": output.get("name"),
                    "check_name": "OCR",
                    "expected": "",
                    "actual": "",
                    "unit": "",
                    "tolerance": "",
                    "tolerance_type": "",
                    "error": f"OCR 단계 실패: {ocr_error}",
                    "limit": "",
                    "label_ok": False,
                    "unit_ok": False,
                    "overall": "ERROR",
                    "ocr_text": "",
                    "image_path": image_path or "",
                })
                continue
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

    def _prepare_setup_connection(self, cases: list[dict] | None = None, *, force: bool = False) -> bool:
        if not force and not self._cases_need_setup_client(cases or []):
            return True

        if not self.connect_manager.SERVER_IP or not self.connect_manager.SETUP_PORT:
            self._load_saved_connection_settings()

        ip = self.connect_manager.SERVER_IP
        setup_port = self.connect_manager.SETUP_PORT
        if not ip or not setup_port:
            self.log("[modbus] setup connection information is missing.")
            return False

        try:
            self.connect_manager.tcp_connect()
        except Exception as exc:
            self.log(f"[modbus] setup reconnect failed: {exc}")
            return False

        ok = self.connect_manager.setup_client is not None and self.connect_manager.is_connected
        product = self.connect_manager.PRODUCT or "A7300"
        if ok:
            self.log(f"[modbus] worker setup connection ready ({product} {ip}:{setup_port})")
        else:
            self.log(f"[modbus] worker setup connection failed ({product} {ip}:{setup_port})")
        return ok

    def _cases_need_setup_client(self, cases: list[dict]) -> bool:
        for case in cases:
            if case.get("setup_modbus") or case.get("measurement_modbus"):
                return True
        return False

    def _load_saved_connection_settings(self):
        try:
            from models import config as app_config
            from models.database import load_setting

            product = load_setting(app_config.KEY_PRODUCT)
            if product and product != self.connect_manager.PRODUCT:
                self.connect_manager.set_product(product)

            ip = load_setting(app_config.KEY_TCP_IP)
            if ip and not self.connect_manager.SERVER_IP:
                self.connect_manager.ip_connect(ip)

            setup_port = load_setting(app_config.KEY_SETUP_PORT)
            if setup_port and not self.connect_manager.SETUP_PORT:
                self.connect_manager.sp_update(int(setup_port))

            touch_port = load_setting(app_config.KEY_TOUCH_PORT)
            if touch_port and not self.connect_manager.TOUCH_PORT:
                self.connect_manager.tp_update(int(touch_port))
        except Exception as exc:
            self.log(f"[modbus] loading saved connection settings failed: {exc}")

    def _unlock_setup(self):
        """(공용 로직: function/modbus_unlock.py — 스펙은 제품 config 모듈)

        표준 실패 처리: critical 스텝 실패 시 예외 → 케이스 중단.
        (이전에는 에러 확인 없이 조용히 진행했음)
        """
        from function.modbus_unlock import unlock_setup
        client = self.connect_manager.setup_client
        if client is None:
            return
        product = self.connect_manager.PRODUCT or "A7300"
        if unlock_setup(client, product, log=self.log):
            return

        self.log(f"[unlock] setup unlock failed ({product}); reconnecting setup client and retrying once")
        if self._prepare_setup_connection(force=True):
            client = self.connect_manager.setup_client
            if client is not None and unlock_setup(client, product, log=self.log):
                return

        raise RuntimeError(f"setup unlock failed ({product})")

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
        """스크린샷 + OCR. 반환: (saved_path, ocr_with_boxes, ocr_error).

        ocr_error 는 스크린샷/OCR 단계 자체가 실패했을 때의 사유 문자열
        (정상이면 None). 호출부에서 검증 대상이 있으면 ERROR 처리에 사용.
        """
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
        ocr_error = None
        if image_path:
            try:
                cropped, _names, boxes = self.yolo.yolo_basic(image_path, return_boxes=True)
                ocr_with_boxes = self.paddleocr.paddleocr_basic(image=cropped, boxes=boxes)
            except Exception as e:
                ocr_error = str(e)
                self.log(f"[ocr] failed: {e}")
        else:
            ocr_error = "screenshot 이미지 없음"
        return saved_path, ocr_with_boxes, ocr_error

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
        fixed_tokens = ocr_eval.fixed_text_tokens(ocr_tokens, units)
        ok, details = ocr_eval.match_fixed_texts(required_texts, fixed_tokens)

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
        label_ok = (not required) or ocr_eval.contains_required(joined, required)

        expected = check.get("expected")
        unit = check.get("unit") or ""
        actual = ocr_eval.measurement_number(tokens, unit)
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
        if text and ocr_eval.contains_required(text, required):
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
