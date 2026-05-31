"""
설정 변경 프로세스.

흐름 (한 항목 한 값에 대해):
    1. unlock (setup_lock + control_lock 시퀀스, 매핑 있는 lock만)
    2. Modbus write_value (제품에 매핑이 있을 때만; 없으면 skip)
    3. Modbus read_value (write 시도했을 때만; 결과 매칭)
    4. uitest_mode_start
    5. main_menu + side_menu + data_view (+ password) + popup/number + apply
    6. screenshot → YOLO crop → PaddleOCR
    7. expected display 가 OCR 결과에 있으면 PASS

검증 철학:
    터치 시퀀스는 "변경 외 다른 의미가 없는" 결정적 동작.
    변경 후 expected가 보이면 성공, 안 보이면 실패. 다른 셀 비교는 불필요.
"""

import csv
import os
import shutil
import time
import traceback
from datetime import datetime

from function.func_touch import TouchManager
from function.func_modbus import ModbusLabels
from function.func_connection import ConnectionManager
from function.func_ocr import PaddleOCRManager, YoloManager
from function.func_evaluation import Evaluation
from config.a7300 import ConfigMap
from config.config_touch import ConfigTouch
from config.config_product import get_map_module
from demo_test.demo_process import get_image_directory


paddleocr_func = PaddleOCRManager()
yolo_func = YoloManager()


def make_result(item, value):
    return {
        "name": item.get("name", "?"),
        "value": value,
        "write": None,
        "read_ok": None,
        "read_value": None,
        "ocr_ok": None,
        "ocr_expected": None,
        "ocr_text": "",         # 전체 OCR 결과 (CSV용)
        "ocr_match": "",        # 변경한 셀에서 매칭된 텍스트 (UI용)
        "screenshot": None,
        "defaults_ok": None,         # 다른 셀이 디폴트값 유지하는가
        "defaults_mismatches": "",   # 불일치 항목 목록
        "note": "",
    }


class SetupTestRunner:

    def __init__(self, base_save_path=None, log_callback=None):
        self.connect_manager = ConnectionManager()
        self.touch_manager = TouchManager()
        self.modbus_label = ModbusLabels()
        self.eval_manager = Evaluation()

        self.product = self.connect_manager.PRODUCT or "A7300"
        try:
            self.cfg_map = get_map_module(self.product).ConfigMap
        except Exception as e:
            print(f"[setup_test] ConfigMap load failed ({self.product}): {e}")
            self.cfg_map = ConfigMap

        self.base_save_path = base_save_path
        self.log = log_callback or print
        self.stop_requested = False

    def cancel(self):
        self.stop_requested = True

    def clear_cancel(self):
        self.stop_requested = False

    def _resolve_addr(self, member_default):
        if member_default is None:
            return None
        name = getattr(member_default, "name", None)
        if not name:
            return None
        try:
            return self.cfg_map[name].value
        except (KeyError, AttributeError):
            return None

    def preflight(self) -> bool:
        ok = True
        self.log(f"[preflight] product={self.product}")
        if self.product != "A7300":
            try:
                from device import get_device_io
                io = get_device_io(self.product)
                connected = io.ping()
                self.log(f"[preflight] bridge ping -> connected={connected}")
                if not connected:
                    ok = False
            except Exception as e:
                self.log(f"[preflight] bridge unreachable: {e}")
                ok = False
        client = self.connect_manager.setup_client
        if client is None:
            self.log("[preflight] setup_client = None")
            ok = False
        else:
            try:
                resp = client.read_holding_registers(3060, count=1)
                self.log(f"[preflight] modbus read 3060 -> "
                         f"{'error' if resp.isError() else f'OK regs={resp.registers}'}")
            except Exception as e:
                self.log(f"[preflight] modbus probe failed: {e}")
                ok = False
        return ok

    def _unlock_setup(self):
        client = self.connect_manager.setup_client
        if not client:
            self.log("[unlock] setup_client missing -> skip")
            return False
        sequences = [
            ("addr_setup_lock", [2300, 0, 700, 1]),
            ("addr_control_lock", [2300, 0, 1600, 1]),
        ]
        any_done = False
        for member_name, vals in sequences:
            try:
                addr_t = self.cfg_map[member_name].value
            except (KeyError, AttributeError):
                self.log(f"[unlock] {member_name} not mapped on {self.product} -> skip")
                continue
            addr = addr_t[0]
            for v in vals:
                if self.stop_requested:
                    break
                try:
                    client.write_register(addr, v)
                except Exception as e:
                    self.log(f"[unlock] write {member_name}({addr})={v} failed: {e}")
                    break
                time.sleep(0.6)
            self.log(f"[unlock] {member_name}@{addr} sequence done")
            any_done = True
        return any_done

    def _write_value(self, item, value):
        client = self.connect_manager.setup_client
        if not client:
            return None
        addr_t = self._resolve_addr(item.get("addr"))
        if addr_t is None:
            self.log(f"[write] {item['name']} addr not mapped on {self.product} -> skip")
            return None
        access_t = self._resolve_addr(item.get("access_addr"))
        try:
            if access_t:
                if isinstance(access_t, dict):
                    client.read_holding_registers(**access_t)
                else:
                    client.read_holding_registers(access_t[0], count=access_t[1])
            if item.get("type") == "uint32":
                hi = (value >> 16) & 0xFFFF
                lo = value & 0xFFFF
                client.write_registers(addr_t[0], [hi, lo])
            else:
                client.write_register(addr_t[0], value)
            if access_t:
                if isinstance(access_t, dict):
                    client.write_register(access_t["address"], 1)
                else:
                    client.write_register(access_t[0], 1)
            time.sleep(0.3)
            self.log(f"[write] {item['name']} @ {addr_t[0]} = {value}")
            return True
        except Exception as e:
            self.log(f"[write] {item['name']} failed: {e}")
            return False

    def _read_value(self, item):
        client = self.connect_manager.setup_client
        if not client:
            return None
        addr_t = self._resolve_addr(item.get("addr"))
        if addr_t is None:
            return None
        # A3700N: Module Setup read 전 access fetch 트리거 (없으면 stale 값)
        if self.product == "A3700N":
            access_t = self._resolve_addr(item.get("access_addr"))
            if access_t:
                try:
                    if isinstance(access_t, dict):
                        client.read_holding_registers(**access_t)
                    else:
                        client.read_holding_registers(access_t[0], count=access_t[1])
                    time.sleep(0.2)
                except Exception as e:
                    self.log(f"[read] fetch trigger failed: {e}")
        try:
            if item.get("type") == "uint32":
                resp = client.read_holding_registers(addr_t[0], count=2)
                if resp.isError():
                    return None
                regs = resp.registers
                v = (regs[0] << 16) | regs[1]
            else:
                resp = client.read_holding_registers(addr_t[0], count=1)
                if resp.isError():
                    return None
                v = resp.registers[0]
            self.log(f"[read]  {item['name']} @ {addr_t[0]} = {v}")
            return v
        except Exception as e:
            self.log(f"[read] {item['name']} failed: {e}")
            return None

    def _navigate_and_input(self, item, value):
        nav = item.get("touch_nav", {}) or {}

        if nav.get("main_menu"):
            self.touch_manager.touch_menu(nav["main_menu"])
        if nav.get("side_menu"):
            self.touch_manager.touch_menu(nav["side_menu"])
        if nav.get("data_view"):
            self.touch_manager.touch_menu(nav["data_view"])
        if nav.get("password"):
            self.touch_manager.touch_password()

        time.sleep(0.5)

        input_type = item.get("input_type", "popup")
        if input_type == "popup":
            opts = item.get("popup_options", {}) or {}
            if value not in opts:
                self.log(f"[nav] popup_options has no value={value} -> skip input")
                return False
            self.touch_manager.touch_menu(opts[value])
            time.sleep(0.3)
            self.touch_manager.touch_menu(ConfigTouch.touch_btn_popup_enter.value)
        elif input_type == "number":
            key_type = item.get("key_type")
            self.touch_manager.input_number(str(value), key_type=key_type)
            time.sleep(0.3)
            self.touch_manager.touch_menu(ConfigTouch.touch_btn_popup_enter.value)
        else:
            self.log(f"[nav] unknown input_type: {input_type}")
            return False

        time.sleep(0.5)
        self.touch_manager.touch_menu(ConfigTouch.touch_btn_apply.value)
        time.sleep(0.5)
        return True

    def _verify_ocr(self, item, value):
        """변경 후 화면 캡처 → OCR → expected 매칭.
        반환: (ocr_ok, expected_text, ocr_text, saved_path)"""
        time.sleep(0.6)
        if self.product != "A7300":
            start_time = datetime.now()
        else:
            start_time = self.modbus_label.system_time_read()

        try:
            self.touch_manager.screenshot()
        except Exception as e:
            self.log(f"[ocr] screenshot failed: {e}")
            return None, None, "", None

        search_pattern = os.path.join(get_image_directory(), "**", "*.png")
        try:
            image_path = self.eval_manager.load_image_file(search_pattern, start_time)
        except Exception as e:
            self.log(f"[ocr] load_image_file failed: {e}")
            image_path = None

        if not image_path:
            self.log(f"[ocr] screenshot file not found")
            return None, None, "screenshot not found", None

        # 결과 폴더로 복사
        saved_path = None
        if self.base_save_path:
            try:
                os.makedirs(self.base_save_path, exist_ok=True)
                base = os.path.basename(image_path)
                safe = item["name"].replace(" ", "_")
                saved_path = os.path.join(self.base_save_path, f"{safe}_{value}_{base}")
                k = 0
                while os.path.exists(saved_path):
                    k += 1
                    saved_path = os.path.join(self.base_save_path,
                                              f"{safe}_{value}_{k}_{base}")
                shutil.copy(image_path, saved_path)
                self.log(f"[ocr] saved: {saved_path}")
            except Exception as e:
                self.log(f"[ocr] copy failed: {e}")
                saved_path = image_path

        try:
            cropped, names = yolo_func.yolo_basic(image_path)
            ocr_results = paddleocr_func.paddleocr_basic(image=cropped) or []
        except Exception as e:
            self.log(f"[ocr] YOLO/OCR failed: {e}")
            return None, None, f"yolo/ocr error: {e}", saved_path

        ocr_text = " | ".join(str(r) for r in ocr_results)

        display_map = item.get("display_map") or {}
        expected = display_map.get(value) if display_map else None
        if expected is None:
            expected = str(value)

        # 매칭된 OCR 텍스트만 추출 (UI 표시용)
        matched_text = ""
        for r in ocr_results:
            if expected in str(r):
                matched_text = str(r).strip()
                break

        match = bool(matched_text)
        self.log(f"[ocr] expected={expected!r}  match={match}  matched_text={matched_text!r}")
        return match, expected, ocr_text, matched_text, saved_path

    def run_single_item(self, item, callback=None):
        # 항목 시작 전 모든 설정 초기화 (Modbus)
        self.log(f"\n[init-before] {item['name']} 시작 전 setup_initialization 호출")
        try:
            self.modbus_label.setup_initialization()
        except Exception as e:
            self.log(f"[init-before] 예외: {e}")

        results = []
        for value in item.get("values", []):
            if self.stop_requested:
                break

            self.log(f"\n{'='*60}")
            self.log(f"=== {item['name']} <- {value} (product={self.product})")
            self.log(f"{'='*60}")

            r = make_result(item, value)
            try:
                self._unlock_setup()

                w = self._write_value(item, value)
                r["write"] = w

                if w is True:
                    rv = self._read_value(item)
                    r["read_value"] = rv
                    r["read_ok"] = (rv == value)

                self.touch_manager.uitest_mode_start()
                self._navigate_and_input(item, value)

                ocr_ok, expected, ocr_text, ocr_match, saved = self._verify_ocr(item, value)
                r["ocr_ok"] = ocr_ok
                r["ocr_expected"] = expected
                r["ocr_text"] = ocr_text
                r["ocr_match"] = ocr_match
                r["screenshot"] = saved

                # 다른 셀 디폴트값 보존 검증 (Modbus read 기반)
                # 변경한 항목의 실제 주소를 except 로 전달 -> alias 자동 처리
                except_addr = self._resolve_addr(item.get("addr"))
                try:
                    defaults_ok, mismatches = self.modbus_label.verify_setup_defaults(
                        except_addr_tuple=except_addr
                    )
                    r["defaults_ok"] = defaults_ok
                    r["defaults_mismatches"] = " | ".join(
                        f"{n}={a}(exp{e})" for n, e, a in mismatches
                    ) if mismatches else ""
                except Exception as e:
                    self.log(f"[verify_defaults] exception: {e}")
                    r["defaults_ok"] = None
                    r["defaults_mismatches"] = f"EXC: {e}"

                summary_pass = (
                    (r["read_ok"] in (True, None))
                    and (r["ocr_ok"] is True)
                    and (r["defaults_ok"] in (True, None))
                )
                r["note"] = "PASS" if summary_pass else "FAIL"
                self.log(f"[done] {item['name']}={value}  "
                         f"write={w} read={r['read_value']} ocr_ok={ocr_ok} "
                         f"-> {r['note']}")
            except Exception as e:
                traceback.print_exc()
                r["note"] = f"Exception: {e}"
                self.log(f"[done] {item['name']}={value} exception: {e}")

            results.append(r)
            if callback:
                try:
                    callback(r)
                except Exception as e:
                    self.log(f"[callback] exception: {e}")
            self._save_csv_row(r)

        # 항목 끝난 후 모든 설정 초기화 (다음 항목/세션을 위한 cleanup)
        self.log(f"\n[init-after] {item['name']} 끝난 후 setup_initialization 호출")
        try:
            self.modbus_label.setup_initialization()
        except Exception as e:
            self.log(f"[init-after] 예외: {e}")

        return results

    def _save_csv_row(self, result):
        if not self.base_save_path:
            return
        try:
            os.makedirs(self.base_save_path, exist_ok=True)
            path = os.path.join(self.base_save_path, "setup_results.csv")
            new = not os.path.exists(path)
            with open(path, "a", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                if new:
                    w.writerow([
                        "timestamp", "name", "value",
                        "write", "read_ok", "read_value",
                        "ocr_ok", "expected", "ocr_match", "ocr_text_full",
                        "defaults_ok", "defaults_mismatches",
                        "screenshot", "note",
                    ])
                w.writerow([
                    datetime.now().isoformat(timespec="seconds"),
                    result.get("name"),
                    result.get("value"),
                    result.get("write"),
                    result.get("read_ok"),
                    result.get("read_value"),
                    result.get("ocr_ok"),
                    result.get("ocr_expected"),
                    result.get("ocr_match"),
                    result.get("ocr_text"),
                    result.get("defaults_ok"),
                    result.get("defaults_mismatches"),
                    result.get("screenshot"),
                    result.get("note"),
                ])
        except Exception as e:
            self.log(f"[csv] save failed: {e}")
