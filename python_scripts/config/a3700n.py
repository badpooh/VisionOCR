# -*- coding: utf-8 -*-
"""A3700N 제품 설정 통합 모듈 (Modbus map + ROI).

A3700N 의 ConfigMap 은 자체 본문이 있고, ConfigROI 는 A7300 base 를
상속해서 override 만 하는 구조다.

신규(단일 진입점):
    config.a3700n.ConfigMap
    config.a3700n.ConfigROI
    config.a3700n.Configs
"""

from .config_map_a3700n import ConfigMap  # noqa: F401  (자체 본문)
from .config_roi_a3700n import ConfigROI, Configs  # noqa: F401  (A7300 base + override)

# Modbus 언락 시퀀스 — (주소, 키 시퀀스, critical).
# 주소는 ConfigMap.addr_control_lock (2902) 단일 소스에서 참조.
# 실행 로직: function/modbus_unlock.py
UNLOCK_SEQUENCE = [
    (ConfigMap.addr_control_lock.value[0], [2300, 0, 1600, 1], True),
]
