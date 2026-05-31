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
