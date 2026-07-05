from pymodbus.client import ModbusTcpClient as ModbusClient
import threading
import time

from models import config as app_config


class ConnectionManager:

    _instance = None

    # 단일 소스: models/config.py
    SUPPORTED_PRODUCTS = app_config.SUPPORTED_PRODUCTS
    DEFAULT_PRODUCT = app_config.DEFAULT_PRODUCT

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ConnectionManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.SERVER_IP = None  # 장치 IP 주소
            self.TOUCH_PORT = None  # 터치 포트
            self.SETUP_PORT = None  # 설정 포트
            self.PRODUCT = self.DEFAULT_PRODUCT  # 선택된 제품 모델
            self.is_connected = False
            self.touch_client = None
            self.setup_client = None
            self._monitor_thread = None
            self.initialized = True

    # Modbus 응답 타임아웃(초). 미지정 시 pymodbus 기본값에 의존하게 되어
    # 환경에 따라 대기가 길어질 수 있으므로 명시한다.
    MODBUS_TIMEOUT = 5

    def ip_connect(self, selected_ip):
        self.SERVER_IP = selected_ip
        print(f"IP set to: {self.SERVER_IP}")

    def tp_update(self, selected_tp):
        self.TOUCH_PORT = selected_tp

    def sp_update(self, selected_sp):
        self.SETUP_PORT = selected_sp

    def set_product(self, product):
        """UI ComboBox에서 선택한 제품 모델을 반영한다.
        지원 목록에 없으면 기본값으로 돌아간다."""
        previous = self.PRODUCT
        if product in self.SUPPORTED_PRODUCTS:
            self.PRODUCT = product
        else:
            print(f"[WARN] Unknown product '{product}', falling back to {self.DEFAULT_PRODUCT}")
            self.PRODUCT = self.DEFAULT_PRODUCT
        print(f"Product set to: {self.PRODUCT}")

        # 제품이 실제로 바뀌면 이전 제품용 DeviceIO(브릿지 연결 등)를 정리한다.
        # 미정리 시 이전 제품의 연결이 남아 다음 테스트를 오염시킬 수 있음.
        if previous != self.PRODUCT:
            from device import loader as device_loader  # 지연 import (계층 분리)
            device_loader.clear_cache()
            print(f"Device IO cache cleared ({previous} -> {self.PRODUCT})")
        
    # 가상 터치 포트(Touch Port 5100) 를 가진 제품 = 외부소스 인가 테스트 모드 지원 제품.
    # 단일 소스: models/config.py.EXTERNAL_SOURCE_TEST_MODE_PRODUCTS

    def _uses_native_touch(self) -> bool:
        return self.PRODUCT in app_config.EXTERNAL_SOURCE_TEST_MODE_PRODUCTS

    def tcp_connect(self):
        if not self.SERVER_IP or not self.SETUP_PORT:
            print("Cannot connect: IP or SETUP PORT is missing.")
            return

        # 재연결 시 기존 소켓이 남아있으면 먼저 정리 (소켓 누수 방지)
        if self.setup_client is not None:
            try:
                self.setup_client.close()
            except Exception as e:
                print(f"[tcp_connect] old setup_client close failed: {e}")
        if self.touch_client is not None:
            try:
                self.touch_client.close()
            except Exception as e:
                print(f"[tcp_connect] old touch_client close failed: {e}")

        # setup_client 는 모든 제품 공통 (측정값 read / setup write 용 Modbus 502).
        # A2700: 브릿지의 _mb (= reg 234=1 보낸 'remote control 세션') 와는
        # 반드시 별개 connection. 브릿지 _mb 로 setup write 보내면 device 가
        # silently drop 함. Device 는 multi-client 허용하므로 두 connection
        # 공존 가능. (자세한 디버깅 기록: vision/docs/a2700_modbus_debugging.md)
        self.setup_client = ModbusClient(
            self.SERVER_IP, port=self.SETUP_PORT, timeout=self.MODBUS_TIMEOUT
        )
        setup_ok = self.setup_client.connect()

        if self._uses_native_touch():
            # A7300: 가상 터치 포트(5100) 도 필요.
            if not self.TOUCH_PORT:
                print("Cannot connect: TOUCH PORT is missing for A7300.")
                return
            self.touch_client = ModbusClient(
                self.SERVER_IP, port=self.TOUCH_PORT, timeout=self.MODBUS_TIMEOUT
            )
            touch_ok = self.touch_client.connect()
            if touch_ok and setup_ok:
                self.is_connected = True
                print("is connected (A7300: touch+setup)")
            else:
                if not touch_ok:
                    print("Failed to connect touch_client")
                if not setup_ok:
                    print("Failed to connect setup_client")
        else:
            # 브릿지 제품군(A3700N, A2700, ...): setup_client 만 연결.
            # 터치/스크린샷은 브릿지(127.0.0.1:5580) 가 담당하므로 여기서
            # touch_client 는 None 으로 둔다. (is_connected 는 setup 기준.)
            self.touch_client = None
            if setup_ok:
                self.is_connected = True
                print(f"is connected ({self.PRODUCT}: setup only, touch via bridge)")
            else:
                print("Failed to connect setup_client")

    def check_connection(self):
        while self.is_connected:
            if self.touch_client is not None and not self.touch_client.is_socket_open():
                print("Touch client disconnected, reconnecting...")
                # 재연결 전 기존 소켓 정리 — close 없이 connect 하면 내부
                # 상태가 불명확해지고 이전 소켓이 누수됨.
                try:
                    self.touch_client.close()
                except Exception:
                    pass
                if self.touch_client.connect():
                    print("touch_client connected")
            if self.setup_client is not None and not self.setup_client.is_socket_open():
                print("Setup client disconnected, reconnecting...")
                try:
                    self.setup_client.close()
                except Exception:
                    pass
                if self.setup_client.connect():
                    print("setup_client connected")
            time.sleep(1)

    def start_monitoring(self):
        self.tcp_connect()
        # 이미 모니터링 스레드가 살아있으면 중복 생성하지 않는다
        # (connect 재시도 시 스레드가 계속 늘어나는 것 방지).
        if self._monitor_thread is not None and self._monitor_thread.is_alive():
            return
        self._monitor_thread = threading.Thread(
            target=self.check_connection, daemon=True
        )
        self._monitor_thread.start()

    def tcp_disconnect(self):
        if self.touch_client is not None:
            self.touch_client.close()
        if self.setup_client is not None:
            self.setup_client.close()
        self.is_connected = False
        print("is disconnected")
