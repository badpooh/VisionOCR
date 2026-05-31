# -*- coding: utf-8 -*-
# A3700N 제품 전용 ROI 설정.
#
# 현재 A3700N 은 Meter 화면 구성이 A7300 과 거의 동일하고 Relay 부분만 다르다.
# 따라서 기본값은 A7300 값을 그대로 재사용하고, 차이가 나는 항목만
# 이 파일 아래쪽에서 오버라이드한다.
#
# TODO(A3700N):
#   - Relay 관련 ROI / 모드버스 주소 오버라이드
#   - 실제 장치에서 촬영한 스크린샷으로 좌표 보정
#
# 사용 방법:
#   from config.config_product import get_roi_module
#   roi_mod = get_roi_module("A3700N")
#   Configs = roi_mod.Configs
#   ConfigROI = roi_mod.ConfigROI

from .config_roi_a7300 import *  # noqa: F401,F403
from .config_roi_a7300 import ConfigROI, Configs  # 명시적 재노출

# ------------------------------------------------------------
# A3700N 전용 오버라이드 영역 (필요할 때 여기에 추가)
# 예) Configs.roi_params[ConfigROI.some_key] = (x, y, w, h)
# ------------------------------------------------------------
