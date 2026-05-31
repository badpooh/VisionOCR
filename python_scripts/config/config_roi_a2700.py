# -*- coding: utf-8 -*-
# A2700 제품 전용 ROI 설정.
#
# 현재는 A7300 값을 그대로 재사용하는 스켈레톤 상태이다.
# 실제 A2700 장치에서 화면 구성을 확인한 뒤, 아래 오버라이드 영역에
# 차이가 나는 좌표/모드버스 주소만 덮어쓴다.
#
# TODO(A2700):
#   - 화면 해상도 / 회전 방향 확인
#   - Meter / Relay ROI 좌표 보정
#   - 모드버스 레지스터 맵 확인
#
# 사용 방법:
#   from config.config_product import get_roi_module
#   roi_mod = get_roi_module("A2700")
#   Configs = roi_mod.Configs
#   ConfigROI = roi_mod.ConfigROI

from .config_roi_a7300 import *  # noqa: F401,F403
from .config_roi_a7300 import ConfigROI, Configs  # 명시적 재노출

# ------------------------------------------------------------
# A2700 전용 오버라이드 영역 (필요할 때 여기에 추가)
# 예) Configs.roi_params[ConfigROI.some_key] = (x, y, w, h)
# ------------------------------------------------------------
