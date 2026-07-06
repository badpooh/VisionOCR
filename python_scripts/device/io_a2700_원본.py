# -*- coding: utf-8 -*-
"""A2700 제품용 DeviceIO — 브릿지(a3700n_bridge 와 동일 프로토콜) REST 호출.

A7300 만 펌웨어 네이티브 Modbus 터치/캡처를 지원하고, 그 외 제품(A2700, A3700N
등) 은 전부 별도 브릿지 앱을 통해 텔넷 → cap.sh / tap.sh 로 동작한다.

따라서 A2700DeviceIO 도 A3700N 과 동일하게 로컬 브릿지의 REST API 를
호출한다. 필요 시 base_url / 포트만 다르게 생성해서 별도 브릿지 인스턴스를
붙이면 된다.
"""

from __future__ import annotations

from .io_a3700n import A3700NDeviceIO


class A2700DeviceIO(A3700NDeviceIO):
    """A2700 — 현재는 A3700N 과 동일한 브릿지 REST 프로토콜 사용.

    실기에서 차이(해상도, 회전, 터치 좌표계 등) 가 확인되면 이 클래스에서
    오버라이드하면 됨.
    """

    product = "A2700"
