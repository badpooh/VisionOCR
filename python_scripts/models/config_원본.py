# Database Keys
KEY_TCP_IP = "LAST_TCP_IP"
KEY_SETUP_PORT = "LAST_SETUP_PORT"
KEY_TOUCH_PORT = "LAST_TOUCH_PORT"
KEY_PRODUCT = "LAST_PRODUCT"

# Supported products (UI ComboBox 선택 목록 / DB 저장값 검증용)
PRODUCT_A7300 = "A7300"
PRODUCT_A3700N = "A3700N"
PRODUCT_A2700 = "A2700"
SUPPORTED_PRODUCTS = (PRODUCT_A7300, PRODUCT_A3700N, PRODUCT_A2700)
DEFAULT_PRODUCT = PRODUCT_A7300

# ----------------------------------------------------------------------------
# UI 테스트 모드 — 추후 3가지로 나뉠 예정.
#
# 현재 코드는 한 가지 라벨(`uses_native_modbus_ui`)로만 분기하지만, 실제로는
# 다음 3가지 모드가 추후 별도 흐름으로 제작될 예정이다:
#
#   1) 외부 소스 인가 테스트 모드 (EXTERNAL_SOURCE_TEST_MODE)
#      - 외부에서 전압/전류 소스를 인가한 뒤 측정값이 맞는지 확인
#      - 펌웨어 가상 터치 모드(Modbus 5100 포트 또는 동등 메커니즘)로 화면 조작
#      - A7300 만 펌웨어 지원
#
#   2) 데모 테스트 모드 (DEMO_TEST_MODE)
#      - 외부 소스 없이 펌웨어 데모 모드 진입 후 측정값 검증
#      - A7300, A3700N (브릿지 경로) 모두 지원
#
#   3) 설정 모드 (SETUP_TEST_MODE)
#      - setup_client(Modbus 502) 통해 설정값 변경 → OCR 로 화면 반영 확인
#      - A7300, A3700N 모두 지원
#
# 현재 구버전 코드의 `_NATIVE_MODBUS_PRODUCTS` / `NATIVE_MODBUS_PRODUCTS` 4곳은
# 모두 (1) 의 의미였으므로 EXTERNAL_SOURCE_TEST_MODE_PRODUCTS 로 합친다.
# 추후 (2)(3) 흐름이 제작되면 해당 set 을 사용하도록 호출부를 업데이트한다.
# ----------------------------------------------------------------------------

EXTERNAL_SOURCE_TEST_MODE_PRODUCTS = (PRODUCT_A7300,)
DEMO_TEST_MODE_PRODUCTS = (PRODUCT_A7300, PRODUCT_A3700N, PRODUCT_A2700)
SETUP_TEST_MODE_PRODUCTS = (PRODUCT_A7300, PRODUCT_A3700N, PRODUCT_A2700)

# 브릿지가 디바이스 Modbus 502 를 점유하는 제품군.
# VisionOCR 측에서 setup_client 를 따로 붙이면 디바이스가 multi-client 거부로
# 브릿지 세션을 kick out → 5900 RemoteControl 까지 끊겨서 touch/screenshot 깨짐.
# 이 set 안의 제품은 ConnectionManager.tcp_connect() 가 setup_client 를 만들지 않음.
# (Modbus read/write 가 필요해지면 브릿지 측에 passthrough 엔드포인트를 추가해야 함.)
BRIDGE_OWNS_MODBUS_PRODUCTS = (PRODUCT_A2700,)

# 하위 호환 (기존 호출자 점진 마이그레이션) — 의미는 (1) 외부소스 인가 모드.
# 새 코드는 EXTERNAL_SOURCE_TEST_MODE_PRODUCTS 를 직접 사용 권장.
NATIVE_MODBUS_PRODUCTS = EXTERNAL_SOURCE_TEST_MODE_PRODUCTS
