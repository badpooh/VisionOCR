# -*- coding: utf-8 -*-
"""xlsx 기반 Setup 테스트 러너.

각 케이스 = 한 (addr, target_value) 시험.

흐름:
    1. is_init → setup_initialization() 만 호출
    2. 일반 케이스:
       a. unlock (control_lock 시퀀스)
       b. access_addr 채워졌으면 read_holding_registers (fetch trigger)
       c. write target_value to addr (value_type 따라 변환)
       d. access_addr 채워졌으면 write 1 (commit)
       e. read back (필요 시 access read 한 번 더 후) → 값 비교
       f. UI 메뉴 터치 → password → input(popup/number) → apply
       g. screenshot → OCR (박스 좌표 동봉)
       h. ROI 필터 → multiset 비교
       i. verify_defaults (옵션)

PASS 조건: read_ok ∧ ocr_ok ∧ defaults_ok (None 은 PASS 로 취급)
"""

from __future__ import annotations

import os
import time
import traceback
from collections import Counter
from datetime import datetime

from .setup_xlsx_loader import load_setup_cases


# ----------------------------------------------------------------------------
# value_type 매핑
# ----------------------------------------------------------------------------
TYPE_WORDS = {
    "uint16": 1, "int16": 1,
    "uint32": 2, "int32": 2,
    "float": 2,
}

PASSWORD_MHN_SEQUENCE = [
    (150, 370),
    (315, 250),
    (150, 370),
    (600, 250),
    (600, 250),
    (370, 250),
    (260, 250),
    (345, 370),
    (425, 310),
    (660, 200),
    (345, 430),
]


def _is_inside_roi(box, roi):
    if roi is None:
        return True
    cx = (box[0] + box[2]) / 2
    cy = (box[1] + box[3]) / 2
    return roi[0] <= cx <= roi[2] and roi[1] <= cy <= roi[3]


class SetupRunner:
    """xlsx 케이스를 순차 실행."""

    def __init__(self, log_callback=None):
        from function.func_touch import TouchManager
        from function.func_modbus import ModbusLabels
        from function.func_evaluation import Evaluation
        from function.func_ocr import PaddleOCRManager, YoloManager
        from function.func_connection import ConnectionManager

        self.touch_manager = TouchManager()
        self.modbus_label = ModbusLabels()
        self.eval_manager = Evaluation()
        self.paddleocr = PaddleOCRManager()
        self.yolo = YoloManager()
        self.connect_manager = ConnectionManager()
        self.log = log_callback or print
        self.stop_requested = False

    def cancel(self):
        self.stop_requested = True

    def _run_touch_actions(self, actions):
        for action in actions or []:
            if isinstance(action, dict) and action.get("front_button"):
                self.touch_manager.button(action["front_button"])
            else:
                self.touch_manager.touch_menu(list(action))
            time.sleep(0.3)

    def _touch_password(self, mode):
        mode = (mode or "M").upper()
        if mode == "MHN":
            self._run_touch_actions(PASSWORD_MHN_SEQUENCE)
            return
        self.touch_manager.touch_password()
        time.sleep(0.3)

    def run(self, base_save_path: str, search_pattern: str,
            product: str = "A3700N", xlsx_path: str = None,
            cases: list = None, result_callback=None):
        if cases is None:
            try:
                cases = load_setup_cases(product, xlsx_path=xlsx_path)
            except FileNotFoundError as e:
                self.log(f"[setup runner] {e}")
                return []
        self.log(f"[setup runner] {len(cases)} case(s) ready for {product}")

        os.makedirs(base_save_path, exist_ok=True)
        results = []
        for i, case in enumerate(cases, 1):
            if self.stop_requested:
                self.log("[setup runner] canceled")
                break
            self.log(f"[setup runner] ({i}/{len(cases)}) {case['name']}")
            try:
                res = self._run_one(case, base_save_path, search_pattern)
            except Exception as e:
                traceback.print_exc()
                res = {"name": case["name"], "overall": "ERROR", "error": str(e)}
            res["index"] = i
            results.append(res)
            self.log(f"  -> {res.get('overall')}")
            if result_callback is not None:
                try:
                    result_callback(res)
                except Exception as e:
                    self.log(f"[setup runner] result_callback failed: {e}")
        return results

    # ------------------------------------------------------------
    # Apply Defaults — Modbus 만으로 default 값 일괄 write.
    # 터치/OCR 없음. setup_client 가 None 이면 (A2700 등) 전부 SKIP.
    # ------------------------------------------------------------
    def apply_defaults(self, cases: list, result_callback=None) -> list:
        results = []

        if self.connect_manager.setup_client is None:
            msg = (f"setup_client 없음 (PRODUCT="
                   f"{self.connect_manager.PRODUCT}). "
                   f"Modbus passthrough 미구현 — 추후 지원.")
            self.log(f"[apply_defaults] {msg}")
            for i, case in enumerate(cases, 1):
                res = {"name": case["name"], "overall": "SKIP",
                       "error": msg, "index": i}
                results.append(res)
                if result_callback is not None:
                    try:
                        result_callback(res)
                    except Exception:
                        pass
            return results

        # ─── 케이스를 access_addr 별로 그룹핑 ───
        # 같은 access (예: M&C 의 51360) 를 공유하는 케이스들은 한 번의
        # atomic FC 16 write 로 모두 commit. Modbus Poll 의 "edit cells →
        # write all" 동일 패턴.
        groups = {}      # access_key -> [(idx, case)]
        skipped = []     # SKIP 으로 처리할 case 들
        for i, case in enumerate(cases, 1):
            addr = case.get("addr")
            access_addr = case.get("access_addr")
            target_values = case.get("target_value") or []
            addr_value = target_values[0] if len(target_values) > 0 else None
            if addr is None or addr_value is None or access_addr is None:
                skipped.append((i, case, "addr/access/value 비어있음"))
                continue
            key = (access_addr[0], access_addr[1])
            groups.setdefault(key, []).append((i, case))

        # SKIP 들 먼저 결과로
        for i, case, note in skipped:
            res = {"name": case["name"], "overall": "SKIP",
                   "note": note, "index": i}
            results.append(res)
            if result_callback is not None:
                try:
                    result_callback(res)
                except Exception:
                    pass

        # ─── 그룹별 batch atomic write ───
        for access_key, group_cases in groups.items():
            if self.stop_requested:
                self.log("[apply_defaults] canceled")
                break

            acc_addr = access_key[0]
            self.log(f"[apply_defaults] === group access={acc_addr} "
                     f"with {len(group_cases)} cases ===")

            # 그룹 내 max(target_addr + words) 로 read 범위 결정
            max_end = acc_addr + 1
            for _, case in group_cases:
                addr = case["addr"]
                max_end = max(max_end, addr[0] + addr[1])
            count = max_end - acc_addr

            try:
                # 1. Unlock 한 번만 (사용자 commui~ 에서 이미 풀어놨더라도
                #    안전하게 한 번 더 — Modbus Poll trace 에서 unlock 이
                #    안 보였던 건 capture 전에 이미 풀려있었기 때문)
                if not self._unlock_setup():
                    raise RuntimeError("control_lock 미매핑")

                # 2. Wide read — setup buffer 로딩 + 우리 로컬 buffer
                client = self.connect_manager.setup_client
                self.log(f"[apply_defaults] FC3 read addr={acc_addr} count={count}")
                rr = client.read_holding_registers(acc_addr, count=count)
                if rr is None or (hasattr(rr, "isError") and rr.isError()):
                    raise RuntimeError(f"read failed: {rr}")
                regs = list(rr.registers)
                self.log(f"[apply_defaults] read result: {regs}")
                if len(regs) < count:
                    raise RuntimeError(
                        f"read short ({len(regs)} < {count})"
                    )

                # 3. 모든 target 자리 수정
                for _, case in group_cases:
                    addr = case["addr"]
                    types = case.get("value_type") or []
                    addr_type = types[0] if len(types) > 0 else "uint16"
                    target_values = case.get("target_value") or []
                    addr_value = target_values[0]
                    target_words = self._encode_value(addr_value, addr_type, client)
                    offset = addr[0] - acc_addr
                    for k, w in enumerate(target_words):
                        regs[offset + k] = int(w) & 0xFFFF

                # 4. 변경할 (addr, value) 페어 리스트 만듦 — 각 case 의
                #    target 만, encode 한 word 들 펼쳐서. 같은 access_addr
                #    아래 여러 case 가 묶여있어도 변경된 register 만 write.
                writes = []
                for _, case in group_cases:
                    addr = case["addr"]
                    types = case.get("value_type") or []
                    addr_type = types[0] if len(types) > 0 else "uint16"
                    target_values = case.get("target_value") or []
                    addr_value = target_values[0]
                    target_words = self._encode_value(
                        addr_value, addr_type, client
                    )
                    for k, w in enumerate(target_words):
                        writes.append((addr[0] + k, int(w) & 0xFFFF))
                writes.sort(key=lambda p: p[0])

                # 5. FC 6 으로 변경된 register 만 한 번에 하나씩 write.
                #    A2700 펌웨어가 FC 16 (multi-write) 를 setup 영역에서
                #    제대로 처리 안 하는 듯해서 single-register write 만 사용.
                for waddr, wval in writes:
                    self.log(f"[apply_defaults] FC6 write {waddr}={wval}")
                    rr = client.write_register(waddr, wval)
                    if rr is None or (hasattr(rr, "isError") and rr.isError()):
                        raise RuntimeError(
                            f"FC6 write {waddr}={wval} failed: {rr}"
                        )
                    time.sleep(0.05)

                # 6. access=1 commit (FC 6, 모든 data write 끝난 후 마지막)
                self.log(f"[apply_defaults] FC6 write access {acc_addr}=1 (commit)")
                rr = client.write_register(acc_addr, 1)
                if rr is None or (hasattr(rr, "isError") and rr.isError()):
                    raise RuntimeError(f"access commit failed: {rr}")
                time.sleep(0.5)

                # 그룹 내 모든 case 를 PASS 로
                for i, case in group_cases:
                    types = case.get("value_type") or []
                    target_values = case.get("target_value") or []
                    res = {"name": case["name"], "overall": "PASS",
                           "addr": case["addr"],
                           "target_value": target_values, "index": i}
                    results.append(res)
                    self.log(f"  -> [{i}] {case['name']} PASS")
                    if result_callback is not None:
                        try:
                            result_callback(res)
                        except Exception as e:
                            self.log(
                                f"[apply_defaults] callback failed: {e}"
                            )

            except Exception as e:
                traceback.print_exc()
                # 그룹 전체를 ERROR 로
                for i, case in group_cases:
                    res = {"name": case["name"], "overall": "ERROR",
                           "error": str(e), "index": i}
                    results.append(res)
                    self.log(f"  -> [{i}] {case['name']} ERROR: {e}")
                    if result_callback is not None:
                        try:
                            result_callback(res)
                        except Exception:
                            pass

        return results

    def _encode_value(self, value, value_type, client):
        """target value 를 register words list 로 인코딩."""
        t = (value_type or "uint16").lower()
        if t == "uint16":
            return [int(value) & 0xFFFF]
        if t == "int16":
            v = int(value)
            if v < 0:
                v = (v + 0x10000) & 0xFFFF
            return [v]
        if t == "uint32":
            v = int(value) & 0xFFFFFFFF
            return [(v >> 16) & 0xFFFF, v & 0xFFFF]
        if t == "int32":
            v = int(value)
            if v < 0:
                v = (v + 0x100000000) & 0xFFFFFFFF
            return [(v >> 16) & 0xFFFF, v & 0xFFFF]
        if t == "uint64":
            v = int(value) & 0xFFFFFFFFFFFFFFFF
            return [(v >> 48) & 0xFFFF, (v >> 32) & 0xFFFF,
                    (v >> 16) & 0xFFFF, v & 0xFFFF]
        if t == "int64":
            v = int(value)
            if v < 0:
                v = (v + 0x10000000000000000) & 0xFFFFFFFFFFFFFFFF
            return [(v >> 48) & 0xFFFF, (v >> 32) & 0xFFFF,
                    (v >> 16) & 0xFFFF, v & 0xFFFF]
        if t == "float":
            return list(client.convert_to_registers(
                float(value), client.DATATYPE.FLOAT32, word_order="big"
            ))
        return [int(value) & 0xFFFF]

    # ------------------------------------------------------------
    # Modbus 헬퍼
    # ------------------------------------------------------------
    def _unlock_setup(self):
        """control_lock 시퀀스로 lock 풀기.

        A7300/A3700N: ConfigMap.addr_control_lock + key [2300, 0, 1600, 1]
        A2700:        와이어 50999 (사양 51000) + key [2300, 0, 700, 1]
                      (A2700 사양서 'Remote Setup Unlock' 항목 그대로)

        같은 modbus connection 내에서 unlock 한 번 한 후 후속 write 들은
        모두 적용. 새 connection 마다 다시 unlock 필요.
        """
        client = self.connect_manager.setup_client
        if client is None:
            return False
        product = self.connect_manager.PRODUCT or "A7300"

        # A2700 — Setup unlock + Control unlock 둘 다 풀어둠
        if product == "A2700":
            # Setup unlock — 와이어 50999 (사양 51000), key [2300, 0, 700, 1]
            for v in [2300, 0, 700, 1]:
                rr = client.write_register(50999, v)
                if rr is None or (hasattr(rr, "isError") and rr.isError()):
                    self.log(f"[setup] A2700 setup unlock write {v} failed: {rr}")
                    return False
                time.sleep(0.4)
            # Control unlock — 와이어 54999 (사양 55000), key [2300, 0, 1600, 1]
            for v in [2300, 0, 1600, 1]:
                rr = client.write_register(54999, v)
                if rr is None or (hasattr(rr, "isError") and rr.isError()):
                    self.log(f"[setup] A2700 control unlock write {v} failed: {rr}")
                    # control unlock 실패해도 setup 은 가능하니 계속 진행
                time.sleep(0.4)
            return True

        # A7300 / A3700N — 기존 경로
        from config.config_product import get_map_module
        try:
            cfg_map = get_map_module(product).ConfigMap
            ctrl_addr = cfg_map.addr_control_lock.value
        except (KeyError, AttributeError, Exception) as e:
            self.log(f"[setup] addr_control_lock not in ConfigMap: {e}")
            return False
        for v in [2300, 0, 1600, 1]:
            client.write_register(ctrl_addr[0], v)
            time.sleep(0.4)
        return True

    def _write_value(self, addr_meta, value, value_type):
        """addr_meta = (addr, words) 튜플. value_type 에 따라 word 인코딩 후
        FC6 (write single register) 만 사용해서 word 단위로 순차 write.

        A2700 펌웨어가 setup 영역에서 FC16 (write_multiple_registers) 를 제대로
        처리하지 못해 옆 register 가 garbage 가 되는 케이스가 있어서 (예전
        디버깅에서 확인), apply_defaults 와 동일한 FC6-only 패턴 사용.
        """
        client = self.connect_manager.setup_client
        if client is None or addr_meta is None or value is None:
            return
        addr = addr_meta[0]
        words = self._encode_value(value, value_type, client)
        for i, w in enumerate(words):
            rr = client.write_register(addr + i, int(w) & 0xFFFF)
            if rr is None or (hasattr(rr, "isError") and rr.isError()):
                raise RuntimeError(
                    f"FC6 write {addr+i}={w} ({value_type}) failed: {rr}"
                )
            time.sleep(0.05)

    def _read_value(self, addr_meta, value_type):
        client = self.connect_manager.setup_client
        if client is None or addr_meta is None:
            return None
        addr, words = addr_meta[0], addr_meta[1]
        resp = client.read_holding_registers(addr, count=words)
        if resp.isError():
            return None
        regs = resp.registers
        t = (value_type or "uint16").lower()
        if t == "uint16":
            return regs[0]
        if t == "int16":
            v = regs[0]
            return v - 0x10000 if v & 0x8000 else v
        if t == "uint32":
            return (regs[0] << 16) | regs[1] if len(regs) >= 2 else regs[0]
        if t == "int32":
            v = (regs[0] << 16) | regs[1] if len(regs) >= 2 else regs[0]
            return v - 0x100000000 if v & 0x80000000 else v
        if t == "uint64":
            if len(regs) < 4:
                return regs[0]
            return ((regs[0] & 0xFFFF) << 48) | ((regs[1] & 0xFFFF) << 32) \
                   | ((regs[2] & 0xFFFF) << 16) | (regs[3] & 0xFFFF)
        if t == "int64":
            if len(regs) < 4:
                return regs[0]
            v = ((regs[0] & 0xFFFF) << 48) | ((regs[1] & 0xFFFF) << 32) \
                | ((regs[2] & 0xFFFF) << 16) | (regs[3] & 0xFFFF)
            return v - 0x10000000000000000 if v & 0x8000000000000000 else v
        if t == "float":
            return client.convert_from_registers(
                regs, client.DATATYPE.FLOAT32, word_order="big"
            )
        return regs[0]

    def _read_access(self, access_meta, target_meta=None):
        """access 레지스터 read.

        target_meta=(addr, words) 가 주어지면 access 부터 target+words 까지
        한 번의 FC 3 read 요청으로 묶어서 읽는다. A2700 firmware 가 요청
        범위에 따라 setup buffer 를 populating 하는 동작이라, narrow read
        (count=1) 만 하면 setup buffer 가 채워지지 않아 후속 write/commit
        이 stale buffer 위에서 일어나 적용 안 됨. Modbus Poll 같은 도구가
        쓰는 방식과 일치시킴.
        """
        client = self.connect_manager.setup_client
        if client is None or access_meta is None:
            return
        acc_addr = access_meta[0]
        acc_words = access_meta[1]
        if target_meta is None:
            client.read_holding_registers(acc_addr, count=acc_words)
            return
        tgt_addr = target_meta[0]
        tgt_words = target_meta[1]
        end = max(acc_addr + acc_words, tgt_addr + tgt_words)
        count = max(1, end - acc_addr)
        client.read_holding_registers(acc_addr, count=count)

    def _atomic_setup_write(self, access_meta, addr_meta, value, value_type):
        print(f"[ATOMIC] called with access={access_meta} addr={addr_meta} val={value}")
        """Modbus Poll 방식 — access ~ target 범위를 한 번에 read 해서 setup
        buffer 에 active 값 로딩, 로컬에서 target 자리 + access[0]=1 로 수정,
        FC 16 write_registers 로 전체 범위를 atomic 하게 write.

        A2700 처럼 'access=1 commit' 메커니즘이 별도 write 로는 안 통하고
        atomic write 로만 적용되는 펌웨어에 대응.

        Returns True 성공 / False 실패.
        """
        client = self.connect_manager.setup_client
        if (client is None or access_meta is None or addr_meta is None
                or value is None):
            return False

        acc_addr = access_meta[0]
        tgt_addr = addr_meta[0]
        tgt_words = addr_meta[1]
        if tgt_addr < acc_addr:
            return False
        count = (tgt_addr + tgt_words) - acc_addr
        if count < 1:
            return False

        # 1. wide read — 현재 active 값으로 setup buffer 로딩 + 우리 로컬 buffer
        rr = client.read_holding_registers(acc_addr, count=count)
        if rr is None or (hasattr(rr, "isError") and rr.isError()):
            self.log(f"[setup] atomic_write read failed: {rr}")
            return False
        regs = list(rr.registers)
        if len(regs) < count:
            self.log(f"[setup] atomic_write read short ({len(regs)} < {count})")
            return False

        # 2. target value words 인코딩
        t = (value_type or "uint16").lower()
        if t == "uint16":
            target_words = [int(value) & 0xFFFF]
        elif t == "int16":
            v = int(value)
            if v < 0:
                v = (v + 0x10000) & 0xFFFF
            target_words = [v]
        elif t == "uint32":
            v = int(value) & 0xFFFFFFFF
            target_words = [(v >> 16) & 0xFFFF, v & 0xFFFF]
        elif t == "int32":
            v = int(value)
            if v < 0:
                v = (v + 0x100000000) & 0xFFFFFFFF
            target_words = [(v >> 16) & 0xFFFF, v & 0xFFFF]
        elif t == "float":
            target_words = client.convert_to_registers(
                float(value), client.DATATYPE.FLOAT32, word_order="big"
            )
        else:
            target_words = [int(value) & 0xFFFF]

        # 3. 로컬 buffer 수정 — target 자리에 새 값, access[0]=1 (commit 신호)
        offset = tgt_addr - acc_addr
        for i, w in enumerate(target_words):
            regs[offset + i] = int(w) & 0xFFFF
        regs[0] = 1   # access register = 1 → commit

        # 4. FC 16 atomic write
        rr = client.write_registers(acc_addr, regs)
        if rr is None or (hasattr(rr, "isError") and rr.isError()):
            self.log(f"[setup] atomic_write write failed: {rr}")
            return False
        return True

    def _commit_access(self, access_meta, value=1, value_type="uint16"):
        """access register 에 commit 값 write. 일반적으로 1, 다른 값(예: 0=MCU)
        도 사용자 지정 가능."""
        if access_meta is None:
            return
        # access 도 _write_value 와 동일 변환 사용 (같은 5종 type 지원)
        self._write_value(access_meta, value, value_type)

    # ------------------------------------------------------------
    # OCR 필터/검증
    # ------------------------------------------------------------
    def _filter_by_roi(self, ocr_with_boxes, roi):
        if roi is None:
            return ocr_with_boxes
        return [(t, b) for (t, b) in ocr_with_boxes if _is_inside_roi(b, roi)]

    def _check_text_multiset(self, ocr_tokens, expected):
        ocr_counter = Counter(ocr_tokens)
        expected_counter = Counter(expected)
        missing = [t for t, c in expected_counter.items() if ocr_counter[t] < c]
        extra = []
        for t, c in ocr_counter.items():
            diff = c - expected_counter.get(t, 0)
            if diff > 0:
                extra.append(f"{t} x{diff}")
        return missing, extra

    # ------------------------------------------------------------
    # 한 케이스 실행
    # ------------------------------------------------------------
    def _run_one(self, case, base_save_path, search_pattern):
        if case.get("is_init"):
            # init row → defaults_<product>.xlsx 를 읽어서 apply_defaults 와
            # 동일 경로로 일괄 적용. 파일 없거나 어느 케이스라도 PASS 가 아니면
            # ERROR 반환 → SetupRunner.run() 의 for-loop 가 다음 케이스 진입은
            # 해도 결과 ERROR 가 summary 에 남으니 사용자가 즉시 확인 가능.
            self.log(f"[init] {case['name']} - apply defaults from xlsx")
            try:
                from .setup_xlsx_loader import load_defaults_cases
                product = self.connect_manager.PRODUCT or "A7300"
                defaults_cases = load_defaults_cases(product)
                self.log(
                    f"[init] {len(defaults_cases)} default cases loaded"
                )
                results = self.apply_defaults(defaults_cases)
                bad = [r for r in results
                       if r.get("overall") not in ("PASS",)]
                if bad:
                    names = ", ".join(r.get("name", "?") for r in bad[:3])
                    raise RuntimeError(
                        f"{len(bad)}/{len(results)} default 케이스 미적용 "
                        f"(예: {names})"
                    )
            except Exception as e:
                self.log(f"[init] failed: {e} — 이후 케이스 중단")
                self.stop_requested = True   # 다음 case 진입 시 run() 의 for-loop break
                return {"name": case["name"], "overall": "ERROR",
                        "error": str(e)}
            return {"name": case["name"], "overall": "INIT"}

        addr = case.get("addr")
        access_addr = case.get("access_addr")
        types = case.get("value_type") or []
        addr_type = types[0] if len(types) > 0 else "uint16"
        access_type = types[1] if len(types) > 1 else "uint16"
        target_values = case.get("target_value") or []
        addr_value = target_values[0] if len(target_values) > 0 else None
        access_commit_value = target_values[1] if len(target_values) > 1 else 1

        if addr is None:
            return {"name": case["name"], "overall": "SKIP",
                    "note": "addr 비어있음"}

        # Modbus phase 전체를 client-check 로 가드.
        # setup_client 가 없는 케이스(예: A2700 — 브릿지가 502 점유)는 unlock/
        # write/read-back 모두 skip 하고 UI 터치 + OCR phase 만 진행한다.
        # read_ok 는 None 으로 남겨 평가 단계에서 PASS 로 취급되도록 함.
        read_ok = None
        actual = None
        has_setup_client = self.connect_manager.setup_client is not None

        if not has_setup_client:
            self.log(f"[setup] {case['name']}: no setup_client (bridge-owned Modbus) "
                     f"— skip unlock/write/read phase")
        else:
            # 1. unlock
            ok = self._unlock_setup()
            if not ok:
                return {"name": case["name"], "overall": "ERROR",
                        "error": "control_lock 미매핑"}

            # 2. access read → write target → access commit
            # Wide read (access ~ target+words 한 번에) — A2700 setup buffer
            # populating 트리거. narrow read 면 device 가 buffer 안 채워서
            # 후속 commit 이 stale 상태에서 일어나 적용 안 됨.
            if addr_value is not None:
                try:
                    if access_addr is not None:
                        self._read_access(access_addr, target_meta=addr)
                        time.sleep(0.3)
                    self._write_value(addr, addr_value, addr_type)
                    time.sleep(0.3)
                    if access_addr is not None:
                        self._commit_access(access_addr, access_commit_value, access_type)
                        time.sleep(0.5)
                except Exception as e:
                    return {"name": case["name"], "overall": "ERROR",
                            "error": f"write 실패: {e}"}

            # 3. read back — 동일하게 wide read 로 buffer 채워두고 target read
            if addr_value is not None:
                try:
                    if access_addr is not None:
                        self._read_access(access_addr, target_meta=addr)
                        time.sleep(0.2)
                    actual = self._read_value(addr, addr_type)
                    # float 비교는 미세 오차 허용
                    if addr_type == "float" and actual is not None:
                        read_ok = abs(float(actual) - float(addr_value)) < 1e-3
                    else:
                        read_ok = (actual == addr_value)
                except Exception as e:
                    self.log(f"[setup] read failed: {e}")
                    read_ok = False

        # 4. UI 터치 navigate
        for key in ("main_menu_xy", "side_menu_xy", "data_view_xy"):
            self._run_touch_actions(case.get(key))

        # 5. password
        if case.get("password"):
            self._touch_password(case.get("password"))

        # 6. input — popup_xy 의 좌표 시퀀스를 순차 탭.
        self._run_touch_actions(case.get("popup_xy"))

        # 7. apply
        self._run_touch_actions(case.get("apply_xy"))

        # 8. screenshot + OCR
        time.sleep(1.0)
        start_time = datetime.now()
        self.touch_manager.screenshot()
        image_path = self.eval_manager.load_image_file(search_pattern, start_time)
        ocr_with_boxes = []
        if image_path:
            try:
                cropped, names, boxes = self.yolo.yolo_basic(
                    image_path, return_boxes=True
                )
                ocr_with_boxes = self.paddleocr.paddleocr_basic(
                    image=cropped, boxes=boxes
                )
            except Exception as e:
                self.log(f"[setup] OCR failed: {e}")

        # 9. ROI 필터
        roi = case.get("roi_xy")
        filtered = self._filter_by_roi(ocr_with_boxes, roi)
        ocr_tokens = [t for (t, b) in filtered if t]

        # 10. multiset 비교
        expected = case.get("expected_text") or []
        missing, extra = self._check_text_multiset(ocr_tokens, expected)
        ocr_ok = (len(missing) == 0 and len(extra) == 0)

        # 11. verify_defaults — setup_client 없으면 skip (None = PASS 취급)
        defaults_ok = None
        defaults_mismatches = []
        if case.get("verify_defaults") and has_setup_client:
            try:
                defaults_ok, defaults_mismatches = (
                    self.modbus_label.verify_setup_defaults(
                        except_addr_tuple=addr
                    )
                )
            except Exception as e:
                self.log(f"[setup] verify_defaults failed: {e}")
                defaults_ok = False
                defaults_mismatches = [("EXC", None, str(e))]

        overall = (
            "PASS"
            if (
                (read_ok in (True, None)) and ocr_ok
                and (defaults_ok in (True, None))
            )
            else "FAIL"
        )

        return {
            "name": case["name"],
            "overall": overall,
            "addr": addr,
            "access_addr": access_addr,
            "value_type": types,
            "target_value": target_values,
            "actual_value": actual,
            "read_ok": read_ok,

            "fixed_missing": list(missing) + [f"[unexpected] {x}" for x in extra],
            "ocr_texts": ocr_tokens,
            "image_path": image_path,
            "verify_defaults_ok": defaults_ok,
            "defaults_mismatches": defaults_mismatches,
        }
