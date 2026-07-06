# -*- coding: utf-8 -*-
"""Product-shared demo test runner (xlsx-driven).

흐름:
    1. test_mode_balance_setting() 호출 → 제품별 데모/테스트 모드 진입
    2. config/demo_test_<product>.xlsx 에서 케이스 리스트 로드
    3. 각 케이스마다:
        a. reset_xy 가 있으면 그 좌표 터치 + system_time_read 로 reset_time 기록
        b. main_menu_xy → side_menu_xy → data_view_xy 순서로 터치
        c. screenshot
        d. load_image_file (가장 최근 PNG)
        e. yolo_basic + paddleocr_basic
        f. _eval_demo_case 로 fixed_text + meas + ratio + timestamp 검증
    4. test_mode_off()

OCR 측정값과 선택적 Modbus read 값을 xlsx 기준 범위와 비교한다.
"""

from __future__ import annotations

import os
import re
import struct
import time
import traceback
from collections import Counter
from datetime import datetime, timedelta

from .demo_xlsx_loader import load_demo_cases


_TIMESTAMP_RE = re.compile(r"\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}")


def _parse_numeric(text: str):
    """'220.5 V' → (220.5, 'V'). 매치 실패 시 (None, None)."""
    m = re.match(r"([-+]?\d+\.?\d*)\s*(.*)", str(text).strip())
    if not m or not m.group(1):
        return None, None
    return float(m.group(1)), m.group(2).strip()


def _collect_unit_hits(ocr_clean: list, target_unit: str, other_unit: str) -> list:
    """OCR 토큰들에서 target_unit 에 해당하는 (text, value) 리스트.

    매칭 정책:
      a) 한 토큰에 단위 직접 붙음 (예: '49.8 %', target='%') → hit.
      b) 다른 단위가 한 토큰에 직접 붙음 (target='%' 인데 '24.86 A') → skip.
      c) 분리 숫자 (u=='') → 그 토큰 다음에 먼저 등장하는 단위 토큰을 보고
         target 이 먼저면 hit, other 가 먼저면 skip. 둘 다 없으면 skip.

    target_unit 이 비어있으면 모든 숫자 hit (단위 무관).
    """
    target = (target_unit or "").strip()
    other = (other_unit or "").strip()

    target_idx = []
    other_idx = []
    if target or other:
        for idx, t in enumerate(ocr_clean):
            if target and t == target:
                target_idx.append(idx)
            elif other and t == other:
                other_idx.append(idx)

    hits = []
    for idx, t in enumerate(ocr_clean):
        if _TIMESTAMP_RE.search(str(t)):
            continue
        v, u = _parse_numeric(t)
        if v is None:
            continue
        if not target:
            hits.append((t, v))
            continue
        if u == target:
            hits.append((t, v))
            continue
        if u != "":
            # 다른 단위 한 토큰 매치 → skip
            continue
        # 분리 숫자: 다음 단위 토큰의 종류로 결정
        next_t = next((i for i in target_idx if i > idx), None)
        next_o = next((i for i in other_idx if i > idx), None)
        if next_t is not None and (next_o is None or next_t < next_o):
            hits.append((t, v))
    return hits


def _extract_timestamps(ocr_texts: list):
    """OCR 결과 리스트에서 'YYYY-MM-DD HH:MM:SS' 패턴을 모두 추출.

    Returns: list of (matched_text, datetime). 파싱 실패 항목은 skip.
    """
    out = []
    for t in ocr_texts:
        if not t:
            continue
        for m in _TIMESTAMP_RE.findall(str(t)):
            try:
                dt = datetime.strptime(m, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue
            out.append((m, dt))
    return out


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


def _normalize_match_text(text: str) -> str:
    return "".join(str(text).split()).casefold()


def _text_options(spec: str) -> list[str]:
    return [part.strip() for part in str(spec).split("|") if part.strip()]


def _ratio_text_options(spec: str) -> list[str]:
    return _text_options(spec)


def _ratio_text_option_set(ratio_text: list) -> set[str]:
    options = set()
    for spec in ratio_text:
        for option in _ratio_text_options(spec):
            norm = _normalize_match_text(option)
            if norm:
                options.add(norm)
    return options


def _match_ratio_texts(ratio_text: list, ocr_texts: list) -> tuple[bool, list[str]]:
    ocr_slots = [
        {"text": str(t).strip(), "norm": _normalize_match_text(t), "used": False}
        for t in ocr_texts
        if t and str(t).strip()
    ]
    results = []
    ok = True
    all_option_norms = set()

    for spec in ratio_text:
        options = []
        for option in _ratio_text_options(spec):
            norm = _normalize_match_text(option)
            if norm:
                options.append((norm, option))
                all_option_norms.add(norm)

        matched = None

        for slot in ocr_slots:
            if slot["used"]:
                continue
            if any(slot["norm"] == norm for norm, _option in options):
                slot["used"] = True
                matched = slot["text"]
                break

        if matched is None:
            ok = False
            results.append(f"ratio text '{spec}' -> MISSING")
            continue

        if len(options) > 1:
            results.append(f"ratio text '{spec}' -> PASS (matched '{matched}')")
        else:
            results.append(f"ratio text '{spec}' -> PASS")

    extras = [
        slot["text"]
        for slot in ocr_slots
        if not slot["used"] and slot["norm"] in all_option_norms
    ]
    if extras:
        ok = False
        for text, count in Counter(extras).items():
            suffix = f" x{count}" if count > 1 else ""
            results.append(f"ratio text unexpected '{text}'{suffix} -> FAIL")

    return ok, results


def _match_fixed_texts(expected_texts: list, ocr_texts: list, units: set) -> tuple[bool, list[str]]:
    ocr_slots = [
        {"text": str(t).strip(), "norm": _normalize_match_text(t), "used": False}
        for t in ocr_texts
        if t and str(t).strip()
    ]
    missing = []

    for spec in expected_texts:
        options = []
        for option in _text_options(spec):
            norm = _normalize_match_text(option)
            if norm:
                options.append((norm, option))

        matched = False
        for slot in ocr_slots:
            if slot["used"]:
                continue
            if any(slot["norm"] == norm for norm, _option in options):
                slot["used"] = True
                matched = True
                break
        if not matched:
            missing.append(spec)

    extra = []
    for slot in ocr_slots:
        if slot["used"] or slot["text"] in units:
            continue
        extra.append(slot["text"])

    if extra:
        for text, count in Counter(extra).items():
            missing.append(f"[unexpected] {text} x{count}")

    return (len(missing) == 0), missing


def _eval_demo_case(case: dict, ocr_texts: list) -> dict:
    """단일 케이스 검증.

    1) fixed_text 와 OCR 텍스트 토큰 multiset 비교 (순서 무관, 띄어쓰기/마침표
       그대로). 단위 토큰(meas_unit, ratio_unit)은 자동 제외 — 단위 외 텍스트가
       OCR 에 더 있거나 fixed_text 가 OCR 에 없으면 FAIL.
       숫자/timestamp 토큰도 자동 제외.
    2) meas_low / meas_high 가 list 형태로 들어옴:
        - 길이 0   → 측정값 검증 skip (PASS)
        - 길이 1   → 단일 임계, 모든 OCR 매치에 일률 적용. 1 개 이상 PASS 면 OK.
        - 길이 N   → OCR 매치 N 개와 인덱스 순으로 매칭. 모두 PASS 여야 OK.
        - 그 외 mismatch 는 FAIL + 로그
    3) ratio_text 가 비어있지 않으면 텍스트 매칭(fixed_text 패턴),
       비었고 ratio_low/high 가 채워졌으면 숫자 범위 매칭(meas 패턴).
       둘 다 비면 skip.
    4) timestamp_count 가 채워졌으면 OCR 결과에서 'YYYY-MM-DD HH:MM:SS'
       패턴 추출 → ① 개수 매치, ② case['_reset_time'] 이 있으면 각 ts 가
       reset_time 이후, ③ timestamp_margin_sec 이 있으면 reset_time +
       margin 까지만 PASS. reset_time 없으면 ②③ skip.
    """
    ocr_clean = [t.strip() for t in ocr_texts if t and t.strip()]
    ratio_text = list(case.get("ratio_text") or [])
    ratio_text_expected = _ratio_text_option_set(ratio_text)

    # 1) fixed_text — multiset 비교 (단위 토큰 / 숫자 / timestamp 자동 제외)
    text_tokens = []
    for t in ocr_clean:
        v, _ = _parse_numeric(t)
        if v is not None:
            continue                     # 숫자 토큰 제외
        if _TIMESTAMP_RE.search(t):
            continue                     # timestamp 토큰 제외
        if _normalize_match_text(t) in ratio_text_expected:
            continue                     # ratio text is validated separately
        text_tokens.append(t)

    units = set()
    mu = case.get("meas_unit")
    ru = case.get("ratio_unit")
    if isinstance(mu, str) and mu.strip():
        units.add(mu.strip())
    if isinstance(ru, str) and ru.strip():
        units.add(ru.strip())

    fixed_ok, missing = _match_fixed_texts(
        list(case.get("fixed_text") or []),
        text_tokens,
        units,
    )

    # 결과 표시용으로 missing 에 extra 도 합쳐 보여줌
    # 2) meas
    unit = (case.get("meas_unit") or "")
    if isinstance(unit, str):
        unit = unit.strip()
    lows = list(case.get("meas_low") or [])
    highs = list(case.get("meas_high") or [])

    # 위치 기반 단위 매칭 — 분리 숫자가 다음에 먼저 등장하는 단위 토큰을
    # 보고 자기 단위인지 결정. ratio_unit 과 meas_unit 이 같이 있을 때도
    # 정확히 분리됨.
    numeric_hits = _collect_unit_hits(ocr_clean, unit, case.get("ratio_unit"))

    meas_results = []
    meas_ok = True

    if not lows and not highs:
        pass  # 임계 없음 — meas 검증 skip
    elif len(lows) != len(highs):
        meas_results.append(
            f"임계 low/high 개수 불일치: low={len(lows)} high={len(highs)}"
        )
        meas_ok = False
    else:
        n_thresh = len(lows)
        n_hit = len(numeric_hits)
        if n_thresh == 1:
            low, high = lows[0], highs[0]
            pass_count = 0
            for t, v in numeric_hits:
                if low <= v <= high:
                    pass_count += 1
                    meas_results.append(f"'{t}' -> PASS")
                else:
                    meas_results.append(f"'{t}' -> FAIL (range {low}~{high})")
            if pass_count == 0:
                meas_ok = False
        elif n_thresh == n_hit:
            for (t, v), low, high in zip(numeric_hits, lows, highs):
                if low <= v <= high:
                    meas_results.append(f"'{t}' -> PASS (range {low}~{high})")
                else:
                    meas_results.append(f"'{t}' -> FAIL (range {low}~{high})")
                    meas_ok = False
        else:
            meas_results.append(
                f"임계 {n_thresh} 개 ≠ OCR 매치 {n_hit} 개 (단위='{unit}')"
            )
            meas_ok = False

    # 3) ratio — 텍스트 매칭 우선, 비면 숫자 범위로
    ratio_results = []
    ratio_ok = True
    ratio_lows = list(case.get("ratio_low") or [])
    ratio_highs = list(case.get("ratio_high") or [])

    if ratio_text:
        ratio_ok, ratio_results = _match_ratio_texts(ratio_text, ocr_clean)
    elif ratio_lows or ratio_highs:
        r_unit = (case.get("ratio_unit") or "")
        if isinstance(r_unit, str):
            r_unit = r_unit.strip()
        # meas 와 동일 위치 기반 매칭. other_unit=meas_unit 으로 분리 숫자
        # 충돌 방지.
        r_hits = _collect_unit_hits(ocr_clean, r_unit, case.get("meas_unit"))

        if len(ratio_lows) != len(ratio_highs):
            ratio_results.append(
                f"ratio low/high 개수 불일치: low={len(ratio_lows)} high={len(ratio_highs)}"
            )
            ratio_ok = False
        else:
            n_thresh = len(ratio_lows)
            n_hit = len(r_hits)
            if n_thresh == 1:
                low, high = ratio_lows[0], ratio_highs[0]
                pass_count = 0
                for t, v in r_hits:
                    if low <= v <= high:
                        pass_count += 1
                        ratio_results.append(f"ratio '{t}' -> PASS")
                    else:
                        ratio_results.append(f"ratio '{t}' -> FAIL (range {low}~{high})")
                if pass_count == 0:
                    ratio_ok = False
            elif n_thresh == n_hit:
                for (t, v), low, high in zip(r_hits, ratio_lows, ratio_highs):
                    if low <= v <= high:
                        ratio_results.append(f"ratio '{t}' -> PASS (range {low}~{high})")
                    else:
                        ratio_results.append(f"ratio '{t}' -> FAIL (range {low}~{high})")
                        ratio_ok = False
            else:
                ratio_results.append(
                    f"ratio 임계 {n_thresh} 개 ≠ OCR 매치 {n_hit} 개 (단위='{r_unit}')"
                )
                ratio_ok = False
    # else: ratio 검증 skip

    # 4) timestamp — 개수 + reset_time 이후
    ts_results = []
    ts_ok = True
    ts_count_expected = case.get("timestamp_count")
    if ts_count_expected is not None:
        ts_hits = _extract_timestamps(ocr_clean)
        if len(ts_hits) != ts_count_expected:
            ts_results.append(
                f"timestamp 개수 mismatch: expected={ts_count_expected} found={len(ts_hits)}"
            )
            ts_ok = False
        else:
            ts_results.append(f"timestamp 개수 OK ({ts_count_expected})")

        reset_time = case.get("_reset_time")
        if reset_time is not None and ts_hits:
            margin_sec = case.get("timestamp_margin_sec")
            upper = (
                reset_time + timedelta(seconds=margin_sec)
                if margin_sec is not None else None
            )
            for txt, dt in ts_hits:
                if dt < reset_time:
                    ts_results.append(
                        f"timestamp '{txt}' -> FAIL (before reset {reset_time:%Y-%m-%d %H:%M:%S})"
                    )
                    ts_ok = False
                elif upper is not None and dt > upper:
                    ts_results.append(
                        f"timestamp '{txt}' -> FAIL (after reset+{margin_sec:g}s)"
                    )
                    ts_ok = False
                else:
                    bound = f"reset~+{margin_sec:g}s" if upper is not None else "after reset"
                    ts_results.append(f"timestamp '{txt}' -> PASS ({bound})")
    # else: timestamp 검증 skip

    overall = "PASS" if (fixed_ok and meas_ok and ratio_ok and ts_ok) else "FAIL"
    return {
        "overall": overall,
        "fixed_missing": missing,
        "meas_results": meas_results,
        "meas_pass_count": sum(1 for r in meas_results if "-> PASS" in r),
        "ratio_results": ratio_results,
        "timestamp_results": ts_results,
    }


class DemoRunner:
    """xlsx 에 정의된 데모 테스트 케이스를 순차 실행."""

    def __init__(self, log_callback=None):
        # 지연 import — 본 파일 단독 import 시 무거운 모델 로드 회피
        from function.func_touch import TouchManager
        from function.func_modbus import ModbusLabels
        from function.func_evaluation import Evaluation
        from function.func_ocr import PaddleOCRManager, YoloManager

        self.touch_manager = TouchManager()
        self.modbus_label = ModbusLabels()
        self.connect_manager = self.modbus_label.connect_manager
        self.eval_manager = Evaluation()
        self.paddleocr = PaddleOCRManager()
        self.yolo = YoloManager()
        self.log = log_callback or print
        self.stop_requested = False
        self._last_reset_time = None

    def cancel(self):
        self.stop_requested = True

    def run(self, base_save_path: str, search_pattern: str, product: str = "A3700N",
            xlsx_path: str=None, cases: list=None, result_callback=None):
        """케이스 실행. 결과 dict 리스트 반환.

        - cases 가 주어지면 그 리스트를 그대로 실행 (UI 트리에서 체크된 것만 등).
        - 아니면 xlsx_path 우선, 그것도 없으면 product 기반 default xlsx 로드.
        - result_callback(dict) 가 주어지면 각 케이스 끝날 때마다 호출 — UI 실시간 갱신용.
        """
        def _abort_result(stage: str, err) -> list:
            # 시작 단계 실패를 빈 리스트로 돌려주면 UI 에 아무 흔적이 안 남아
            # 실패가 묻힌다 → 명시적 ERROR row 하나를 결과/콜백으로 남긴다.
            res = {"name": stage, "overall": "ERROR",
                   "error": str(err), "index": 1}
            if result_callback is not None:
                try:
                    result_callback(res)
                except Exception as cb_err:
                    self.log(f"[demo runner] result_callback failed: {cb_err}")
            return [res]

        if cases is None:
            try:
                cases = load_demo_cases(product, xlsx_path=xlsx_path)
            except FileNotFoundError as e:
                self.log(f"[demo runner] {e}")
                return _abort_result("[xlsx load]", e)
        type(self.paddleocr).reset_cache()
        self.log("[demo runner] OCR cache reset for this run")
        self.log(f"[demo runner] {len(cases)} case(s) ready for {product}")
        self._last_reset_time = None

        # 데모/테스트 모드 진입 (제품별 분기 사용)
        try:
            self.modbus_label.test_mode_balance_setting()
        except Exception as e:
            self.log(f"[demo runner] enter demo mode failed: {e}")
            traceback.print_exc()
            return _abort_result("[demo mode 진입]", e)
        self.log("[demo runner] wait 2.0s for demo mode settle")
        time.sleep(2.0)

        os.makedirs(base_save_path, exist_ok=True)
        results = []
        try:
            for i, case in enumerate(cases, 1):
                if self.stop_requested:
                    self.log("[demo runner] canceled")
                    break
                self.log(f"[demo runner] ({i}/{len(cases)}) {case['name']}")
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
                        self.log(f"[demo runner] result_callback failed: {e}")
        finally:
            try:
                self.modbus_label.test_mode_off()
            except Exception as e:
                self.log(f"[demo runner] test_mode_off failed: {e}")
            try:
                type(self.paddleocr).reset_cache()
                self.log("[demo runner] OCR cache reset after run")
            except Exception as e:
                self.log(f"[demo runner] OCR cache reset failed: {e}")

        return results

    def _read_modbus_measurements(self, case: dict) -> tuple[list[str], bool]:
        """Read optional Modbus values from the case and check low/high ranges."""
        addresses = list(case.get("modbus_addr") or [])
        if not addresses:
            return [], True

        results = []
        lows = list(case.get("modbus_low") or [])
        highs = list(case.get("modbus_high") or [])
        value_types = list(case.get("modbus_type") or ["float"])
        unit = str(case.get("modbus_unit") or "").strip()

        if len(lows) != len(highs):
            return [
                f"Modbus range mismatch: low={len(lows)} high={len(highs)}"
            ], False
        if not lows:
            return ["Modbus range missing"], False

        if len(lows) == 1:
            ranges = [(lows[0], highs[0])] * len(addresses)
        elif len(lows) == len(addresses):
            ranges = list(zip(lows, highs))
        else:
            return [
                f"Modbus range count mismatch: addr={len(addresses)} range={len(lows)}"
            ], False

        if not value_types:
            value_types = ["float"]
        if len(value_types) == 1:
            value_types = value_types * len(addresses)
        elif len(value_types) != len(addresses):
            return [
                f"Modbus type count mismatch: addr={len(addresses)} type={len(value_types)}"
            ], False

        client = self.connect_manager.setup_client
        if client is None:
            return ["Modbus ERROR: setup_client is not connected"], False

        aggre_selection = case.get("modbus_aggre_selection")
        if aggre_selection is not None and self.modbus_label.uses_native_modbus_ui():
            try:
                from config.a7300 import ConfigMap as ConfigMapA7300

                selection = ConfigMapA7300.addr_aggregation_selection.value
                client.read_holding_registers(**selection)
                client.write_register(selection["address"], int(aggre_selection))
                client.read_holding_registers(**selection)
            except Exception as exc:
                self.log(f"[demo runner] aggregation selection failed: {exc}")
                return [f"Modbus aggregation ERROR: {exc}"], False

        all_ok = True
        unit_suffix = f" {unit}" if unit else ""
        for address, value_type, (low, high) in zip(addresses, value_types, ranges):
            if self.stop_requested:
                break
            try:
                doc_address = int(address)
                read_address = doc_address - 1
                if read_address < 0:
                    raise ValueError(f"invalid Modbus address: {doc_address}")
                word_count = _type_words(value_type)
                response = client.read_holding_registers(read_address, count=word_count)
                if response is None or (
                    hasattr(response, "isError") and response.isError()
                ):
                    raise RuntimeError(f"read failed: {response}")

                registers = list(getattr(response, "registers", []) or [])
                if len(registers) < word_count:
                    raise RuntimeError(f"read short: {len(registers)} < {word_count}")

                actual = _decode_register_value(registers, value_type)
                ok = float(low) <= float(actual) <= float(high)
                if not ok:
                    all_ok = False
                results.append(
                    f"Modbus[{doc_address}] {actual:.6g}{unit_suffix} -> "
                    f"{'PASS' if ok else 'FAIL'} "
                    f"(range {low:g}~{high:g}{unit_suffix})"
                )
            except Exception as exc:
                all_ok = False
                results.append(f"Modbus[{address}] ERROR: {exc}")
                self.log(f"[demo runner] modbus read failed ({address}): {exc}")

        return results, all_ok

    def _run_one(self, case: dict, base_save_path: str, search_pattern: str) -> dict:
        # is_init 케이스: setup_initialization 만 호출하고 메뉴/OCR/검증 스킵.
        # enabled 셀에 'init' 적은 케이스가 여기로 들어옴.
        if case.get("is_init"):
            note = "Use Apply Defaults before START for Demo Test initialization"
            self.log(f"[init] {case['name']} - skipped. {note}")
            return {"name": case["name"], "overall": "INIT", "note": note}

        # enabled 셀에 'reset' 적은 케이스는 Max/Min reset 만 수행하고
        # 메뉴/OCR/검증은 스킵한다. 이후 timestamp 검증 기준으로도 재사용한다.
        if case.get("is_reset"):
            reset_action = case.get("reset_action") or "max_min"
            is_demand_sync = (reset_action == "demand_sync")
            is_demand_clear_sync = (reset_action == "demand_clear_sync")
            is_demand_reset = is_demand_sync or is_demand_clear_sync
            if is_demand_clear_sync:
                label = "Demand clear/sync"
            elif is_demand_sync:
                label = "Demand sync"
            else:
                label = "Max/Min reset"
            self.log(f"[reset] {case['name']} - {label}")
            try:
                reset_time = self.modbus_label.system_time_read()
                if is_demand_clear_sync:
                    ok = self.modbus_label.reset_demand_clear_sync_only()
                elif is_demand_sync:
                    ok = self.modbus_label.reset_demand_sync_only()
                else:
                    ok = self.modbus_label.reset_max_min_only()
                if not ok:
                    return {
                        "name": case["name"],
                        "overall": "ERROR",
                        "error": f"{label} failed",
                    }
                self._last_reset_time = reset_time
                time.sleep(0.3)
            except Exception as e:
                self.log(f"[reset] failed: {e}")
                return {"name": case["name"], "overall": "ERROR", "error": str(e)}
            overall = "DEMAND_RESET" if is_demand_reset else "RESET"
            return {"name": case["name"], "overall": overall, "reset_time": reset_time}

        # reset 컬럼이 truthy 면 메뉴 터치 전에 Modbus 로 디바이스 max/min
        # reset 트리거. 단 system_time_read 를 reset 보다 먼저 호출 — reset_time
        # 이 항상 실제 reset 시점보다 앞서므로 OCR 에 잡힌 max/min timestamp
        # 가 reset_time 이전이 되는 역방향 케이스를 원천 차단.
        case.pop("_reset_time", None)
        if case.get("reset"):
            try:
                case["_reset_time"] = self.modbus_label.system_time_read()
                ok = self.modbus_label.reset_max_min_only()
                if not ok:
                    case["_reset_time"] = None
                else:
                    self._last_reset_time = case.get("_reset_time")
                time.sleep(0.3)
            except Exception as e:
                self.log(f"[demo runner] reset/time_read failed: {e}")
                case["_reset_time"] = None
        elif case.get("timestamp_count") is not None and self._last_reset_time is not None:
            case["_reset_time"] = self._last_reset_time

        for key in ("main_menu_xy", "side_menu_xy", "data_view_xy"):
            for action in (case.get(key) or []):
                if isinstance(action, dict) and action.get("front_button"):
                    self.touch_manager.button(action["front_button"])
                    time.sleep(0.3)
                    continue
                self.touch_manager.touch_menu(list(action))
                time.sleep(0.3)

        time.sleep(1.0)
        start_time = datetime.now()
        self.touch_manager.screenshot()
        image_path = self.eval_manager.load_image_file(search_pattern, start_time)
        if not image_path:
            return {"name": case["name"], "overall": "FAIL", "error": "no screenshot"}

        cropped, _names = self.yolo.yolo_basic(image_path)
        ocr_texts = self.paddleocr.paddleocr_basic(image=cropped)

        eval_res = _eval_demo_case(case, ocr_texts)
        modbus_results, modbus_ok = self._read_modbus_measurements(case)
        eval_res["modbus_results"] = modbus_results
        if not modbus_ok:
            eval_res["overall"] = "FAIL"
        eval_res["name"] = case["name"]
        eval_res["image_path"] = image_path
        eval_res["ocr_texts"] = ocr_texts
        return eval_res


# Backward-compatible alias for older imports.
DemoModeA3700NRunner = DemoRunner
