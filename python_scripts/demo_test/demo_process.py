# -*- coding: utf-8 -*-
"""제품별 screenshot 검색 경로 헬퍼.

A7300 만 펌웨어가 UNC share(\\10.10.20.30\screenshot) 에 PNG 를 떨궈주고,
그 외 제품(A3700N, A2700, ...) 은 브릿지가 받은 bytes 를 로컬 디렉터리에
저장한다 → get_image_directory() 로 제품에 맞춰 고른다.

(과거 DemoTest / TestRunnerWorker 흐름은 NewTestWidget +
demo_runner 로 통합되어 제거됨. 본 모듈은 헬퍼 두 개만 보존.)
"""

import os

from function.func_connection import ConnectionManager
from function.func_touch import TouchManager
from models import config as app_config


# A7300 스크린샷 UNC 공유 경로. 환경이 다르면 VISIONOCR_SCREENSHOT_DIR
# 환경변수로 재정의 가능 (미설정 시 기존 기본값 유지).
image_directory = os.environ.get(
    "VISIONOCR_SCREENSHOT_DIR", r"\\10.10.20.30\screenshot"
)


def get_image_directory() -> str:
    """현재 선택된 제품에 맞는 스크린샷 검색 루트 경로.

    A7300 (외부소스 인가 모드) → image_directory/{현재 TCP/IP 주소}
    그 외 (A3700N / A2700 / ...) → TouchManager.bridge_screenshot_dir (로컬)
    """
    try:
        connect_manager = ConnectionManager()
        product = connect_manager.PRODUCT
        server_ip = connect_manager.SERVER_IP
    except Exception:
        product = None
        server_ip = None
    if product in app_config.EXTERNAL_SOURCE_TEST_MODE_PRODUCTS:
        if server_ip:
            return os.path.join(image_directory, str(server_ip))
        return image_directory
    return TouchManager.bridge_screenshot_dir
