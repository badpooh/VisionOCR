# -*- coding: utf-8 -*-
"""DeviceIO — 제품별 터치/스크린샷 추상화.

사용 예:
    from device import get_device_io
    io = get_device_io(ConnectionManager().PRODUCT)
    io.touch(120, 340)
    png = io.screenshot()
"""

from .io_base import DeviceIO, DeviceIOError  # noqa: F401
from .loader import get_device_io  # noqa: F401
