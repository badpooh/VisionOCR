# -*- coding: utf-8 -*-
"""Modbus setup/control 언락 공용 실행기.

언락 스펙(주소/키 시퀀스)은 각 제품 config 모듈의 UNLOCK_SEQUENCE 가
단일 소스다 (config/a2700.py, a3700n.py, a7300.py 참고).
기존에는 setup/clipping/source runner 3곳에 각자 하드코딩돼 있었고,
그로 인해 source runner 가 비-A2700 에서 잘못된 주소(54999)를 쓰는
버그가 있었다 — 이 모듈로 통합.

표준 실패 처리 (setup_runner 방식):
    critical=True 스텝 실패 → 즉시 False 반환 (호출측에서 케이스 중단)
    critical=False 스텝 실패 → 경고 로그 후 계속
"""

from __future__ import annotations

import time


def unlock_setup(client, product: str, log=print, interval_s: float = 0.4) -> bool:
    """제품별 UNLOCK_SEQUENCE 를 실행한다.

    Returns:
        True  — 언락 성공 (non-critical 스텝 실패는 성공으로 간주)
        False — client 없음 / 스펙 미정의 / critical 스텝 실패
    """
    if client is None:
        return False

    from config.config_product import get_map_module
    try:
        sequence = get_map_module(product).UNLOCK_SEQUENCE
    except Exception as e:
        log(f"[unlock] UNLOCK_SEQUENCE not defined for {product}: {e}")
        return False

    for addr, keys, critical in sequence:
        for value in keys:
            try:
                rr = client.write_register(addr, value)
                failed = rr is None or (hasattr(rr, "isError") and rr.isError())
            except Exception as e:
                rr = e
                failed = True
            if failed:
                msg = (f"[unlock] {product} write addr={addr} "
                       f"value={value} failed: {rr}")
                if critical:
                    log(msg)
                    return False
                log(msg + " (non-critical, continue)")
            time.sleep(interval_s)
    return True
