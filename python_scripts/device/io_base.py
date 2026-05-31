# -*- coding: utf-8 -*-
"""DeviceIO 추상 인터페이스.

제품별 구현이 공통으로 노출해야 하는 메서드만 정의한다.
내부에서 Modbus 를 쓸지, HTTP 를 쓸지, 네이티브 펌웨어 API 를 쓸지는
구현체의 자유.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class DeviceIOError(RuntimeError):
    """DeviceIO 계열 공통 예외."""


class DeviceIO(ABC):
    """제품 독립 터치/스크린샷 인터페이스."""

    product: str = "UNKNOWN"

    @abstractmethod
    def touch(self, x: int, y: int) -> None:
        """물리 LCD 좌표 (0..799, 0..479) 에 탭 이벤트 발생."""

    @abstractmethod
    def screenshot(self) -> bytes:
        """현재 LCD 내용을 PNG bytes 로 반환 (180° 회전 적용된 상태)."""

    # 선택 메서드 — 지원 안 하면 그냥 아무 동작 안 함
    def ping(self) -> bool:
        """백엔드가 살아있는지 확인. 기본 구현은 True."""
        return True

    def close(self) -> None:
        """백엔드 자원 해제. 기본은 no-op."""
        return None
