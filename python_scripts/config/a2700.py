# -*- coding: utf-8 -*-
"""A2700 제품 설정 통합 모듈 (Modbus map + ROI).

현재는 A7300 base 를 그대로 재사용하는 스켈레톤.

신규(단일 진입점):
    config.a2700.ConfigMap
    config.a2700.ConfigROI
    config.a2700.Configs
    config.a2700.ConfigInitialValue
"""

from .config_map_a2700 import ConfigMap, ConfigInitialValue  # noqa: F401
from .config_roi_a2700 import ConfigROI, Configs  # noqa: F401

# Modbus 언락 시퀀스 — (주소, 키 시퀀스, critical).
# critical=True 스텝이 실패하면 언락 실패로 중단, False 면 경고 후 계속.
# 와이어 주소 = 사양서 주소 - 1. (A2700 사양서 'Remote Setup Unlock' 항목)
# 실행 로직: function/modbus_unlock.py — 값이 바뀌면 이 파일만 수정.
UNLOCK_SEQUENCE = [
    (50999, [2300, 0, 700, 1], True),    # Setup unlock (사양 51000)
    (54999, [2300, 0, 1600, 1], False),  # Control unlock (사양 55000) — 실패해도 setup 은 가능
]
