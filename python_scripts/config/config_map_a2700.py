# -*- coding: utf-8 -*-
# A2700 제품 전용 Modbus 주소 맵.
#
# 현재는 A7300 의 주소 맵을 그대로 재사용하는 스켈레톤 상태이다.
# 실기에서 A2700 의 Modbus Map 문서를 확인한 뒤, 이 파일 아래쪽에
# 차이가 나는 항목만 오버라이드한다.
#
# TODO(A2700):
#   - 공식 A2700 Modbus Map 문서 확보
#   - Lock / System / Network / Measurement / Event 각 블록의 베이스 주소 확인
#   - A2700 신규/삭제 필드 반영
#
# 사용 방법:
#   from config.config_product import get_map_module
#   cfg_map = get_map_module("A2700").ConfigMap

from .config_map_a7300 import *  # noqa: F401,F403
from .config_map_a7300 import ConfigMap, ConfigInitialValue  # 명시적 재노출

# ------------------------------------------------------------
# A2700 전용 오버라이드 영역 (필요할 때 여기에 추가)
# ------------------------------------------------------------
