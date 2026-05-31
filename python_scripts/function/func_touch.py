import os
import time
from datetime import datetime

from function.func_connection import ConnectionManager
from config.config_touch import ConfigTouch
from models import config as app_config

# 브릿지 제품군(A3700N, A2700, ...) 의 스크린샷 저장 경로.
# A7300 은 펌웨어가 UNC share 에 PNG 를 떨구고 이 경로는 쓰지 않는다.
# (Evaluation.load_image_file 이 YYYYMMDD_HHMMSS 패턴을 glob 하므로 파일명
#  규칙만 맞으면 디렉터리는 어디든 OK. 외부에서 override 가능하게 노출.)
_BRIDGE_SCREENSHOT_DIR_DEFAULT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "bridge_screenshots",
)


class TouchManager:

    connect_manager = ConnectionManager()
    hex_value = int("A5A5", 16)

    # 브릿지 제품군 공용 스크린샷 저장 디렉터리. 외부에서 재지정 가능.
    bridge_screenshot_dir = _BRIDGE_SCREENSHOT_DIR_DEFAULT
    # 하위호환 — 예전 코드가 a3700n_screenshot_dir 를 직접 참조하던 경우.
    a3700n_screenshot_dir = _BRIDGE_SCREENSHOT_DIR_DEFAULT

    # A7300 ConfigTouch 값 → 이름 역조회 캐시. 제품별 좌표 번역에 사용.
    _coord_name_cache = None

    def __init__(self):
        pass

    # ------------------------------------------------------------
    # 제품별 좌표 번역
    # ------------------------------------------------------------
    @classmethod
    def _build_coord_name_map(cls):
        """A7300 ConfigTouch 의 (x, y) → member name 역조회 테이블.

        값이 중복되는 멤버가 있으면(예: touch_toggle_min 과 touch_toggle_thd_ln
        둘 다 [620, 150]) 마지막에 등록된 이름이 이긴다. 테스트 용도라 OK.
        """
        if cls._coord_name_cache is not None:
            return cls._coord_name_cache
        mapping = {}
        for member in ConfigTouch:
            v = member.value
            if (isinstance(v, (list, tuple)) and len(v) == 2
                    and all(isinstance(n, int) for n in v)):
                mapping[(int(v[0]), int(v[1]))] = member.name
        cls._coord_name_cache = mapping
        return mapping

    def _translate_coord_for_product(self, coord):
        """현재 제품에 맞게 좌표를 치환.

        현재는 A3700N 만 별도 프로파일(ConfigTouchA3700N) 이 있음.
        - A7300 값 → 이름(역조회) → A3700N 값 순으로 변환.
        - 테이블에 없으면 원본 좌표 그대로 반환.
        """
        try:
            product = self.connect_manager.PRODUCT
        except AttributeError:
            return coord
        if product != "A3700N":
            return coord
        try:
            x, y = int(coord[0]), int(coord[1])
        except (TypeError, ValueError, IndexError):
            return coord
        name = self._build_coord_name_map().get((x, y))
        if not name:
            return coord
        try:
            from config.config_touch_a3700n import ConfigTouchA3700N
            member = ConfigTouchA3700N[name]
        except (KeyError, ImportError):
            return coord
        new_coord = member.value
        if list(new_coord) != [x, y]:
            print(f"[A3700N] coord remap {name}: ({x},{y}) -> "
                  f"({new_coord[0]},{new_coord[1]})")
        return new_coord

    # ------------------------------------------------------------
    # 제품별 라우팅 헬퍼
    # ------------------------------------------------------------
    def _uses_bridge(self) -> bool:
        """현재 제품이 브릿지 기반인가?

        A7300 만 펌웨어가 Modbus 테스트 모드(가상 터치/캡처) 를 지원.
        그 외(A3700N, A2700, ...) 는 모두 별도 브릿지 앱을 통해
        텔넷 → cap.sh/tap.sh 로 터치/스크린샷을 수행한다.
        """
        try:
            return self.connect_manager.PRODUCT not in app_config.EXTERNAL_SOURCE_TEST_MODE_PRODUCTS
        except AttributeError:
            return False

    # 하위호환 이름 — 구 코드가 _is_a3700n 을 호출할 때 대비.
    def _is_a3700n(self) -> bool:
        try:
            return self.connect_manager.PRODUCT == "A3700N"
        except AttributeError:
            return False

    def _device_io(self):
        """현재 제품용 DeviceIO 인스턴스를 반환.

        device 패키지는 지연 import — A7300 전용 환경에서 import 사이드
        이펙트(urllib 등) 를 최소화하기 위함.
        """
        from device import get_device_io  # 지연 import
        return get_device_io(self.connect_manager.PRODUCT)

    def touch_write(self, address, value, delay=0.6):
        attempt = 0
        while attempt < 2:
            self.connect_manager.touch_client.write_register(address, value)
            read_value = self.connect_manager.touch_client.read_holding_registers(address)
            time.sleep(delay)
            if read_value == value:
                print("\nTouched")
                return
            else:
                attempt += 1

    def uitest_mode_start(self):
        # 브릿지 제품군은 펌웨어 쪽 UI 테스트 모드 플래그가 없음.
        # cap.sh / tap.sh 가 이미 배포된 상태가 곧 테스트 모드에 해당.
        if self._uses_bridge():
            print(f"[{self.connect_manager.PRODUCT}] uitest_mode_start: "
                  f"bridge already in test mode (no-op)")
            return
        if self.connect_manager.touch_client:
            self.touch_write(ConfigTouch.touch_addr_ui_test_mode.value, 1)
        else:
            print("client Error")

    def screenshot(self):
        # 브릿지 제품군: 브릿지에서 PNG bytes 를 받아와 로컬 디렉터리에
        # timestamp 파일명으로 저장. 다운스트림 load_image_file 은
        # search_pattern glob 으로 가장 최근 파일을 고르므로 저장 위치만
        # 일치하면 된다.
        if self._uses_bridge():
            product = self.connect_manager.PRODUCT
            try:
                io = self._device_io()
                png = io.screenshot()
            except Exception as e:
                print(f"[{product}] screenshot failed: {e}")
                return
            try:
                os.makedirs(self.bridge_screenshot_dir, exist_ok=True)
                fname = datetime.now().strftime("%Y%m%d_%H%M%S") + ".png"
                fpath = os.path.join(self.bridge_screenshot_dir, fname)
                with open(fpath, "wb") as f:
                    f.write(png)
                print(f"[{product}] screenshot saved: {fpath}")
            except OSError as e:
                print(f"[{product}] screenshot save failed: {e}")
            return

        # A7300 네이티브 — 기존 Modbus 캡처 트리거.
        if self.connect_manager.touch_client:
            self.touch_write(ConfigTouch.touch_addr_screen_capture.value, self.hex_value)
        else:
            print("client Error")

    def touch_password(self):
        # 브릿지 제품군: Modbus 가상 좌표 대신 브릿지 탭으로 처리. 좌표는
        # A7300 UI 기준이므로 다른 화면과 어긋나면 호출부에서 직접 좌표를
        # 넘기도록 해야 함 — 이 메서드는 호환 용도.
        number0_x = 485
        number0_y = 290
        enter_x = 340
        enter_y = 350

        if self._uses_bridge():
            seq = [(number0_x, number0_y)] * 4 + [(enter_x, enter_y)]
            self.touch_menu(seq)
            return

        if self.connect_manager.touch_client:
            for i in range(4):
                self.touch_write(ConfigTouch.touch_addr_pos_x.value, number0_x)
                self.touch_write(ConfigTouch.touch_addr_pos_y.value, number0_y)
                self.touch_write(ConfigTouch.touch_addr_touch_mode.value, 1)
                self.touch_write(ConfigTouch.touch_addr_touch_mode.value, 0)
            self.touch_write(ConfigTouch.touch_addr_pos_x.value, enter_x)
            self.touch_write(ConfigTouch.touch_addr_pos_y.value, enter_y)
            self.touch_write(ConfigTouch.touch_addr_touch_mode.value, 1)
            self.touch_write(ConfigTouch.touch_addr_touch_mode.value, 0)

    def touch_menu(self, menu_input):
        coords_to_touch = []

        if menu_input:
            if isinstance(menu_input[0], (list, tuple)):
                coords_to_touch = menu_input
            else:
                coords_to_touch = [menu_input]

        # 브릿지 제품군: 브릿지 REST 로 탭 이벤트 전송. Modbus touch_client 없음.
        if self._uses_bridge():
            product = self.connect_manager.PRODUCT
            try:
                io = self._device_io()
            except Exception as e:
                print(f"[{product}] touch_menu device_io error: {e}")
                return
            for coords in coords_to_touch:
                if not isinstance(coords, (list, tuple)) or len(coords) != 2:
                    print(f"Skipping invalid coordinate format: {coords}")
                    continue
                # 제품별 좌표 프로파일로 치환 (A3700N 등).
                coords = self._translate_coord_for_product(coords)
                x, y = coords[0], coords[1]
                try:
                    print(f"[{product}] touch -> ({x},{y})")
                    io.touch(int(x), int(y))
                except Exception as e:
                    print(f"[{product}] touch({x},{y}) failed: {e}")
                    continue
                # A7300 쪽 기본 간격(0.8s)과 유사하게. 브릿지 내부에도 지연이
                # 있지만 연속 탭 간 여유를 좀 더 둔다.
                time.sleep(0.6)
            return

        if self.connect_manager.touch_client:
            for coords in coords_to_touch:
                if not isinstance(coords, (list, tuple)) or len(coords) != 2:
                    print(f"Skipping invalid coordinate format: {coords}")
                    continue
                x, y = coords
                self.touch_write(ConfigTouch.touch_addr_pos_x.value, x)
                self.touch_write(ConfigTouch.touch_addr_pos_y.value, y)
                self.touch_write(ConfigTouch.touch_addr_touch_mode.value, 1) # 누름
                time.sleep(0.2) # 안정성을 위한 딜레이
                self.touch_write(ConfigTouch.touch_addr_touch_mode.value, 0) # 뗌
                time.sleep(0.6) # 다음 터치와의 간격
        else:
            print("Menu Touch Error: Not connected")

    def btn_front_setup(self):
        # 브릿지 제품군은 프런트 하드키 Modbus 매핑이 없음 → 호출 무시.
        # 테스트 시나리오가 이 경로를 타면 호출부에서 명시적 좌표 touch 로
        # 대체해야 한다.
        if self._uses_bridge():
            print(f"[{self.connect_manager.PRODUCT}] btn_front_setup: not supported (no-op)")
            return
        if self.connect_manager.touch_client:
            self.touch_write(ConfigTouch.touch_addr_setup_button.value, 0)
            self.touch_write(ConfigTouch.touch_addr_setup_button_bit.value, 2)
        else:
            print("Front setup button is clicked Error")

    def btn_front_meter(self):
        if self._uses_bridge():
            print(f"[{self.connect_manager.PRODUCT}] btn_front_meter: not supported (no-op)")
            return
        if self.connect_manager.touch_client:
            self.touch_write(ConfigTouch.touch_addr_setup_button.value, 0)
            self.touch_write(ConfigTouch.touch_addr_setup_button_bit.value, 64)
        else:
            print("Front meter button is clicked Error")

    def btn_front_home(self):
        if self._uses_bridge():
            print(f"[{self.connect_manager.PRODUCT}] btn_front_home: not supported (no-op)")
            return
        if self.connect_manager.touch_client:
            self.touch_write(ConfigTouch.touch_addr_setup_button.value, 0)
            self.touch_write(ConfigTouch.touch_addr_setup_button_bit.value, 1)
        else:
            print("Front home button is clicked Error")

    def input_number(self, number_str, key_type=None):
        """
        number_str 예: '123', '100000', '0'
        각 자릿수를 순회하며, 해당 버튼 터치 로직을 수행.
        """
        if key_type == None:
            for digit in number_str:
                if digit == '0':
                    self.touch_menu(ConfigTouch.touch_btn_number_0.value)
                elif digit == '1':
                    self.touch_menu(ConfigTouch.touch_btn_number_1.value)
                elif digit == '2':
                    self.touch_menu(ConfigTouch.touch_btn_number_2.value)
                elif digit == '3':
                    self.touch_menu(ConfigTouch.touch_btn_number_3.value)
                elif digit == '4':
                    self.touch_menu(ConfigTouch.touch_btn_number_4.value)
                elif digit == '5':
                    self.touch_menu(ConfigTouch.touch_btn_number_5.value)
                elif digit == '6':
                    self.touch_menu(ConfigTouch.touch_btn_number_6.value)
                elif digit == '7':
                    self.touch_menu(ConfigTouch.touch_btn_number_7.value)
                elif digit == '8':
                    self.touch_menu(ConfigTouch.touch_btn_number_8.value)
                elif digit == '9':
                    self.touch_menu(ConfigTouch.touch_btn_number_9.value)
                elif digit == '.':
                    self.touch_menu(ConfigTouch.touch_btn_number_dot.value)
                elif digit == '-':
                    self.touch_menu(ConfigTouch.touch_btn_number_minus.value)

                else:
                    print("input number touch error")
        elif key_type == 'ref':
            for digit in number_str:
                if digit == '0':
                    self.touch_menu(ConfigTouch.touch_btn_ref_num_0.value)
                elif digit == '1':
                    self.touch_menu(ConfigTouch.touch_btn_ref_num_1.value)
                elif digit == '2':
                    self.touch_menu(ConfigTouch.touch_btn_ref_num_2.value)
                elif digit == '3':
                    self.touch_menu(ConfigTouch.touch_btn_ref_num_3.value)
                elif digit == '4':
                    self.touch_menu(ConfigTouch.touch_btn_ref_num_4.value)
                elif digit == '5':
                    self.touch_menu(ConfigTouch.touch_btn_ref_num_5.value)
                elif digit == '6':
                    self.touch_menu(ConfigTouch.touch_btn_ref_num_6.value)
                elif digit == '7':
                    self.touch_menu(ConfigTouch.touch_btn_ref_num_7.value)
                elif digit == '8':
                    self.touch_menu(ConfigTouch.touch_btn_ref_num_8.value)
                elif digit == '9':
                    self.touch_menu(ConfigTouch.touch_btn_ref_num_9.value)
                # elif digit == '.':
                #     self.touch_menu(ConfigTouch.touch_btn_ref_num_dot.value)

                else:
                    print("input number touch error")

