# -*- coding: utf-8 -*-
"""A7300 제품용 DeviceIO — 펌웨어 네이티브 Modbus 테스트 모드 사용.

기존 function.func_touch.TouchManager / config.config_touch.ConfigTouch 를
그대로 감싸는 얇은 래퍼. 명령어 이름만 통일한다.

screenshot() 은 A7300 펌웨어 특성 상 레지스터에 0xA5A5 를 쓰면 LCD 가 캡처
동작을 수행한다 (결과 바이트를 어디서 받는지는 기존 코드 흐름에 따름).
이 구현은 일단 "캡처 트리거" 까지만 담당하고 bytes 를 돌려주지 않는다면
DeviceIOError 를 올린다.
"""

from __future__ import annotations

from .io_base import DeviceIO, DeviceIOError


class A7300DeviceIO(DeviceIO):
    product = "A7300"

    def __init__(self):
        # 지연 import: 본 모듈 단독 AST 파싱 시 순환 의존 방지
        from function.func_touch import TouchManager
        from config.config_touch import ConfigTouch

        self._tm = TouchManager()
        self._cfg = ConfigTouch

    # ------------------------------------------------------------
    def touch(self, x: int, y: int) -> None:
        if self._tm.connect_manager.touch_client is None:
            raise DeviceIOError("touch_client not connected")
        self._tm.touch_menu([int(x), int(y)])

    def screenshot(self) -> bytes:
        if self._tm.connect_manager.touch_client is None:
            raise DeviceIOError("touch_client not connected")
        # A7300 펌웨어에 캡처 트리거를 보냄. 실제 이미지 획득은 별도 경로.
        # bytes 반환이 필요한 상위 코드는 아직 이쪽을 쓰지 않음.
        self._tm.screenshot()
        raise DeviceIOError(
            "A7300 native screenshot returns no bytes through this API; "
            "use the existing firmware capture pipeline."
        )
