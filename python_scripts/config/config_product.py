# -*- coding: utf-8 -*-
# 제품(A7300 / A3700N / A2700)별 ROI / Modbus map 모듈 로더.
#
# UI 에서 ComboBox 로 제품을 선택하면 ConnectionManager.PRODUCT 가 갱신된다.
# 화면 좌표나 모드버스 주소가 필요한 코드에서는 아래 get_roi_module() /
# get_map_module() 을 호출해 현재 제품에 맞는 모듈을 받아 Configs / ConfigROI /
# ConfigMap 을 사용한다.
#
# 예:
#   from config.config_product import get_roi_module
#   from function.func_connection import ConnectionManager
#   roi_mod = get_roi_module(ConnectionManager().PRODUCT)
#   Configs = roi_mod.Configs
#   ConfigROI = roi_mod.ConfigROI

import importlib
from models import config as app_config

# 제품 코드 → 통합 모듈(map + roi) 경로 매핑.
# 한 제품의 ConfigMap / ConfigROI / Configs / ConfigInitialValue 가 모두
# 같은 모듈에서 노출되므로, get_map_module / get_roi_module 둘 다 같은 모듈을
# 반환하면 충분하다.
_PRODUCT_MODULES = {
    app_config.PRODUCT_A7300: "config.a7300",
    app_config.PRODUCT_A3700N: "config.a3700n",
    app_config.PRODUCT_A2700: "config.a2700",
}

# 하위 호환: 일부 호출자(setup_process 등)가 get_map_module/get_roi_module 을
# 분리해서 호출하므로, 매핑을 같은 dict 로 가리킨다.
_PRODUCT_ROI_MODULES = _PRODUCT_MODULES
_PRODUCT_MAP_MODULES = _PRODUCT_MODULES

# 한 번 로드한 모듈은 캐싱한다. importlib.import_module 자체도
# sys.modules 캐시를 쓰지만, 미지원 제품 경고를 한 번만 찍기 위해
# 별도로 관리한다.
_module_cache = {}


def _load(product, mapping, kind):
    """공통 모듈 로더. product 가 지원 목록에 없으면 DEFAULT_PRODUCT 로 폴백한다."""
    key = product if product in mapping else app_config.DEFAULT_PRODUCT
    if product and product not in mapping:
        print(
            f"[config_product] Unknown product '{product}' for {kind}, "
            f"falling back to {app_config.DEFAULT_PRODUCT}"
        )
    cache_key = (kind, key)
    if cache_key in _module_cache:
        return _module_cache[cache_key]
    module = importlib.import_module(mapping[key])
    _module_cache[cache_key] = module
    return module


def get_roi_module(product):
    """주어진 제품 코드에 해당하는 ROI 설정 모듈을 돌려준다.

    - 지원 목록에 없거나 None 이면 기본 제품(DEFAULT_PRODUCT)으로 폴백한다.
    - 호출 측에서는 반환된 모듈의 Configs / ConfigROI 를 사용하면 된다.
    """
    return _load(product, _PRODUCT_ROI_MODULES, "roi")


def get_map_module(product):
    """주어진 제품 코드에 해당하는 Modbus 주소 맵 모듈을 돌려준다.

    - 지원 목록에 없거나 None 이면 기본 제품(DEFAULT_PRODUCT)으로 폴백한다.
    - 호출 측에서는 반환된 모듈의 ConfigMap 을 사용하면 된다.
    """
    return _load(product, _PRODUCT_MAP_MODULES, "map")


def supported_products():
    """로더가 매핑을 가지고 있는 제품 목록."""
    return tuple(_PRODUCT_MODULES.keys())
