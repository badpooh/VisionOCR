# -*- coding: utf-8 -*-
"""xlsx 기반 데모 테스트 케이스 로더.

vision/config/demo_test_<product>.xlsx 를 읽어서 케이스 dict 리스트로 반환.

좌표 셀 (`*_xy`)
    "120,50"               → [(120, 50)]
    "120,50; 200,50"       → [(120, 50), (200, 50)]   (세미콜론으로 다중)
    "home; 120,50"         → 전면 Home 버튼 후 좌표 터치
    빈 셀                  → []

임계 셀 (`meas_low`, `meas_high`, `ratio_low`, `ratio_high`)
    220                    → [220.0]                  (단일)
    "220; 218; 222"        → [220.0, 218.0, 222.0]    (세미콜론으로 다중)
    빈 셀                  → []

fixed_text 는 콤마 구분.
ratio_text 는 콤마 또는 세미콜론 구분. 각 항목의 A|B 는 A 또는 B 중 하나를 허용.
reset 은 boolean (TRUE/1/yes/ok = True).
timestamp_count 는 '4' 또는 '4; 600' (개수; 마진초).
"""

from __future__ import annotations

import os


_FRONT_BUTTON_ALIASES = {
    "home": "home",
    "setup": "setup",
    "event": "event",
    "back": "back",
    "esc": "back",
    "escape": "back",
    "localremote": "localremote",
    "faultreset": "faultreset",
    "meter": "meter",
    "relay": "relay",
    "cbon": "cbon",
    "cboff": "cboff",
}


def _normalize_nav_token(token: str) -> str:
    return "".join(ch for ch in token.strip().lower() if ch.isalnum())


def _parse_xy_list(s) -> list:
    """좌표/전면 버튼 action 리스트 반환. 빈 셀이면 [].

    예:
        "100,85"           -> [(100, 85)]
        "home; 100,85"     -> [{"front_button": "home"}, (100, 85)]
    """
    if s is None:
        return []
    if not isinstance(s, str):
        raise ValueError(f"xy 셀은 문자열이어야 함: {type(s).__name__}={s!r}")
    s = s.strip()
    if not s:
        return []
    items = []
    for part in s.split(";"):
        part = part.strip()
        if not part:
            continue
        if "," not in part:
            key = _normalize_nav_token(part)
            if key in _FRONT_BUTTON_ALIASES:
                items.append({"front_button": _FRONT_BUTTON_ALIASES[key]})
                continue
            raise ValueError(f"xy 항목은 'x,y' 또는 전면 버튼 이름이어야 함: {part!r}")

        xy = [p.strip() for p in part.split(",")]
        if len(xy) != 2:
            raise ValueError(f"xy 항목은 'x,y' 형식이어야 함: {part!r}")
        items.append((int(xy[0]), int(xy[1])))
    return items


def _parse_num_list(s) -> list:
    """숫자 list 반환. 단일 값(220) 또는 '220; 218; 222' 둘 다 허용. 빈 셀이면 []."""
    if s is None:
        return []
    if isinstance(s, (int, float)):
        return [float(s)]
    if not isinstance(s, str):
        raise ValueError(f"숫자 셀 타입 미지원: {type(s).__name__}={s!r}")
    s = s.strip()
    if not s:
        return []
    out = []
    for part in s.split(";"):
        part = part.strip()
        if not part:
            continue
        out.append(float(part))
    return out


def _parse_int_list(s) -> list:
    """Semicolon-separated integer list. Blank cells return []."""
    if s is None:
        return []
    if isinstance(s, bool):
        return []
    if isinstance(s, int):
        return [int(s)]
    if isinstance(s, float):
        if s != int(s):
            raise ValueError(f"integer value expected: {s!r}")
        return [int(s)]
    if not isinstance(s, str):
        raise ValueError(f"integer list value unsupported: {type(s).__name__}={s!r}")
    s = s.strip()
    if not s:
        return []
    out = []
    for part in s.split(";"):
        part = part.strip()
        if not part:
            continue
        out.append(int(float(part)))
    return out


def _parse_text_list(s) -> list:
    """Semicolon-separated text list. A single value may apply to all entries."""
    if s is None:
        return []
    if isinstance(s, str):
        return [part.strip() for part in s.split(";") if part.strip()]
    return [str(s).strip()]


def _parse_int_scalar(s):
    values = _parse_int_list(s)
    return values[0] if values else None


def _parse_enabled(s) -> str:
    """enabled 셀 상태 파서 → 'enabled' / 'disabled' / 'init' / 'reset'.

        TRUE / 1 / yes / 빈 셀  → 'enabled' (실행)
        FALSE / 0 / no          → 'disabled' (스킵)
        init / INIT             → 'init' (setup_initialization 만 호출)
        reset / RESET           → 'reset' (Max/Min reset 만 호출)
    """
    if isinstance(s, str):
        value = s.strip().lower()
        if value == "init":
            return "init"
        normalized = "".join(ch for ch in value if ch.isalnum())
        if normalized in ("demandreset", "resetdemand", "demand"):
            return "demand_reset"
        if value in ("reset", "max/min reset", "maxmin reset", "maxminreset"):
            return "reset"
    if s is False:
        return "disabled"
    if isinstance(s, str) and s.strip().lower() in ("false", "0", "no", "n"):
        return "disabled"
    return "enabled"


def _parse_bool(s) -> bool:
    """boolean 셀. True/'TRUE'/'1'/'yes'/'ok' 면 True, 그 외(빈 셀 포함)는 False."""
    if s is None:
        return False
    if isinstance(s, bool):
        return s
    if isinstance(s, (int, float)):
        return bool(s)
    if isinstance(s, str):
        return s.strip().lower() in ("true", "1", "yes", "y", "ok")
    return False


def _parse_count_and_margin(s):
    """timestamp 검증용 (count, margin_sec) 셀 파서.

    형식:
        '4'         → (4, None)              개수만, 마진 없음
        '4; 600'    → (4, 600.0)             개수 + 마진 (초)
        4 (숫자)    → (4, None)
        빈 셀       → (None, None)           검증 skip

    margin 이 None 이면 검증 측에서 reset_time 이후 모두 PASS.
    margin 이 있으면 reset_time ~ reset_time + margin 사이만 PASS.
    """
    if s is None:
        return (None, None)
    if isinstance(s, bool):
        return (None, None)
    if isinstance(s, (int, float)):
        return (int(s), None)
    if not isinstance(s, str):
        return (None, None)
    s = s.strip()
    if not s:
        return (None, None)
    parts = [p.strip() for p in s.split(";") if p.strip()]
    if not parts:
        return (None, None)
    count = int(float(parts[0]))
    margin = float(parts[1]) if len(parts) > 1 else None
    return (count, margin)


def _reset_action(name: str, state: str) -> str:
    normalized_name = "".join(
        ch for ch in str(name or "").lower()
        if ch.isalnum()
    )
    if state == "demand_reset":
        return "demand_sync" if "sync" in normalized_name else "demand_clear_sync"
    if state != "reset":
        return ""
    if "demand" in normalized_name:
        return "demand_sync" if "sync" in normalized_name else "demand_clear_sync"
    return "max_min"


def _parse_fixed_text(s) -> list:
    if s is None:
        return []
    return [t.strip() for t in str(s).split(",") if t.strip()]


def _parse_ratio_text(s) -> list:
    if s is None:
        return []
    text = str(s).replace(";", ",")
    return [t.strip() for t in text.split(",") if t.strip()]


def _xlsx_path(product: str) -> str:
    """config/<제품>/Demo_Test_<모델>.xlsx 경로 (경로 규칙: config.xlsx_paths)."""
    from config.xlsx_paths import xlsx_path
    return xlsx_path("Demo_Test", product)


def load_demo_cases(product: str = "A3700N", xlsx_path: str = None) -> list:
    """xlsx 를 읽어 케이스 리스트 반환. 헤더(1행) + 설명(2행) 다음부터 데이터.

    xlsx_path 가 주어지면 그 경로를 우선 사용. 없으면 product 기반 default
    (config/demo_test_<product>.xlsx).
    """
    from openpyxl import load_workbook

    path = xlsx_path if xlsx_path else _xlsx_path(product)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"demo test xlsx 없음: {path}")

    wb = load_workbook(path, data_only=True, read_only=True)
    try:
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
    finally:
        wb.close()
    if len(rows) < 3:
        return []
    header = [str(h) if h is not None else "" for h in rows[0]]

    cases = []
    for r in rows[2:]:
        if r is None or all(v is None for v in r):
            continue
        # zip 은 짧은 행에서 뒤 컬럼을 조용히 누락시키므로 index-safe 매핑 사용
        record = {key: (r[idx] if idx < len(r) else None)
                  for idx, key in enumerate(header) if key}
        if not record.get("name"):
            continue
        state = _parse_enabled(record.get("enabled"))
        if state == "disabled":
            continue
        ts_count, ts_margin = _parse_count_and_margin(record.get("timestamp_count"))
        reset_action = _reset_action(record.get("name"), state)
        cases.append({
            "name": str(record["name"]).strip(),
            "is_init": (state == "init"),
            "is_reset": (state in ("reset", "demand_reset")),
            "reset_action": reset_action,
            "main_menu_label": record.get("main_menu_label"),
            "main_menu_xy":    _parse_xy_list(record.get("main_menu_xy")),
            "side_menu_label": record.get("side_menu_label"),
            "side_menu_xy":    _parse_xy_list(record.get("side_menu_xy")),
            "data_view_label": record.get("data_view_label"),
            "data_view_xy":    _parse_xy_list(record.get("data_view_xy")),
            "fixed_text":      _parse_fixed_text(record.get("fixed_text")),
            "meas_low":        _parse_num_list(record.get("meas_low")),
            "meas_high":       _parse_num_list(record.get("meas_high")),
            "meas_unit":       record.get("meas_unit"),
            # Optional Modbus communication-value checks. Blank addresses
            # preserve the previous OCR-only demo-test behavior.
            "modbus_addr":     _parse_int_list(record.get("modbus_addr")),
            "modbus_type":     _parse_text_list(record.get("modbus_type")),
            "modbus_low":      _parse_num_list(record.get("modbus_low")),
            "modbus_high":     _parse_num_list(record.get("modbus_high")),
            "modbus_unit":     record.get("modbus_unit"),
            "modbus_aggre_selection": _parse_int_scalar(
                record.get("modbus_aggre_selection")
            ),
            # ratio: 가운데 % / 텍스트 영역. ratio_text 가 채워졌으면 텍스트
            # 매칭, 아니면 ratio_low/high 범위. 둘 다 비면 검증 skip.
            "ratio_low":       _parse_num_list(record.get("ratio_low")),
            "ratio_high":      _parse_num_list(record.get("ratio_high")),
            "ratio_text":      _parse_ratio_text(record.get("ratio_text")),
            "ratio_unit":      record.get("ratio_unit"),
            # reset: truthy 면 메뉴 터치 전에 Modbus 로 디바이스 max/min reset
            # 트리거 → system_time_read 로 reset_time 기록. timestamp 검증의
            # 기준이 된다. falsy 면 skip.
            "reset":           _parse_bool(record.get("reset")),
            # timestamp: '4' → 개수만, '4; 600' → 개수 + 마진(초). 비면 skip.
            # 마진이 있으면 reset_time ~ reset_time + margin 까지 PASS.
            "timestamp_count":      ts_count,
            "timestamp_margin_sec": ts_margin,
            "notes":           record.get("notes"),
        })
    return cases
