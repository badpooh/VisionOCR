# -*- coding: utf-8 -*-
"""제품 코드 → DeviceIO 인스턴스 로더.

config.config_product.get_roi_module / get_map_module 과 같은 패턴.

사용:
    from function.func_connection import ConnectionManager
    from device import get_device_io
    io = get_device_io(ConnectionManager().PRODUCT)
    io.touch(400, 240)
"""

from __future__ import annotations

from typing import Optional

from models import config as app_config

from .io_base import DeviceIO

_instance_cache: dict = {}


def get_device_io(product: Optional[str], **kwargs) -> DeviceIO:
    """주어진 제품 코드에 해당하는 DeviceIO 싱글톤을 돌려준다.

    kwargs 는 각 구현체 생성자에 전달 (예: A3700N 의 base_url).
    - 알 수 없는 제품이면 DEFAULT_PRODUCT 로 폴백.
    """
    key = product if product else app_config.DEFAULT_PRODUCT

    if key == app_config.PRODUCT_A7300:
        cache_key = ("A7300",)
        if cache_key not in _instance_cache:
            from .io_a7300 import A7300DeviceIO
            _instance_cache[cache_key] = A7300DeviceIO(**kwargs)
        return _instance_cache[cache_key]

    if key == app_config.PRODUCT_A3700N:
        # base_url 이 다를 수 있으니 kwargs 키에 포함시켜 캐싱
        cache_key = ("A3700N", tuple(sorted(kwargs.items())))
        if cache_key not in _instance_cache:
            from .io_a3700n import A3700NDeviceIO
            _instance_cache[cache_key] = A3700NDeviceIO(**kwargs)
        return _instance_cache[cache_key]

    if key == app_config.PRODUCT_A2700:
        cache_key = ("A2700",)
        if cache_key not in _instance_cache:
            from .io_a2700 import A2700DeviceIO
            _instance_cache[cache_key] = A2700DeviceIO(**kwargs)
        return _instance_cache[cache_key]

    # 알 수 없는 제품 → 기본값 재귀 호출
    print(f"[device.loader] Unknown product '{product}', "
          f"falling back to {app_config.DEFAULT_PRODUCT}")
    return get_device_io(app_config.DEFAULT_PRODUCT, **kwargs)


def clear_cache() -> None:
    """UI 에서 제품 변경 시 호출."""
    for io in _instance_cache.values():
        try:
            io.close()
        except Exception:
            pass
    _instance_cache.clear()
