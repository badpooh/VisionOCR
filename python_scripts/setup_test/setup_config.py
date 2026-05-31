"""
설정 테스트 항목 정의.

각 항목 구조:
{
    "name": "표시 이름",
    "addr": ConfigMap 멤버 (제품별 ConfigMap에서 같은 이름이 있으면 자동 매핑;
                            매핑 없으면 Modbus write/read 단계 자동 skip),
    "type": "uint16" | "uint32",
    "access_addr": access commit 주소 (옵셔널),
    "values": [테스트할 값 목록],
    "touch_nav": {"main_menu":..., "side_menu":..., "data_view":..., "password": False/False},
    "input_type": "popup" | "number",
    "popup_options": {value: ConfigTouch.x.value, ...},
    "key_type": None | "ref",
    "display_map": {value: 화면 표시 문자열, ...} (None이면 raw 숫자),
}

A3700N Voltage 화면 셀 매핑 (사용자 첨부 사진 기준):
    [320,210] data_view_1 = Wiring
    [620,210] data_view_2 = Min. Measured Secondary Voltage
    [320,280] data_view_3 = PT Primary Voltage [V]
    [620,280] data_view_4 = PT Secondary Voltage [V]
    [320,360] data_view_5 = Reference Voltage [V] (mode/value 통합 popup)
    [620,360] data_view_6 = Sliding Reference Voltage
    [320,430] data_view_7 = Rotating Sequence
    [620,430] data_view_8 = Volt. Phase Selection
"""

from config.a7300 import ConfigMap
from config.config_touch import ConfigTouch


SETUP_GROUPS = {
    "Measurement Setup": {
        "Voltage": [
            # ----- 왼쪽 1행 [320,210] -----
            {
                "name": "Wiring",
                "addr": ConfigMap.addr_wiring,
                "type": "uint16",
                "access_addr": ConfigMap.addr_measurement_setup_access,
                "values": [0, 1, 2, 3],
                "touch_nav": {
                    "main_menu": ConfigTouch.touch_main_menu_1.value,
                    "side_menu": ConfigTouch.touch_side_menu_1.value,
                    "data_view": ConfigTouch.touch_data_view_1.value,
                    "password": False,
                },
                "input_type": "popup",
                "popup_options": {
                    0: ConfigTouch.touch_btn_popup_1.value,
                    1: ConfigTouch.touch_btn_popup_2.value,
                    2: ConfigTouch.touch_btn_popup_3.value,
                    3: ConfigTouch.touch_btn_popup_4.value,
                },
                "display_map": {0: "3P4W", 1: "3P3W", 2: "1P2W", 3: "1P3W"},
            },
            # ----- 오른쪽 1행 [620,210] -----
            {
                "name": "Min Measured Secondary LN Voltage",
                "addr": ConfigMap.addr_min_measured_secondary_ln_voltage,
                "type": "uint16",
                "access_addr": ConfigMap.addr_measurement_setup_access,
                "values": [5],
                "touch_nav": {
                    "main_menu": ConfigTouch.touch_main_menu_1.value,
                    "side_menu": ConfigTouch.touch_side_menu_1.value,
                    "data_view": ConfigTouch.touch_data_view_2.value,
                    "password": False,
                },
                "input_type": "number",
                "key_type": None,
                "display_map": None,
            },
            # ----- 왼쪽 2행 [320,280] -----
            {
                "name": "VT Primary LL Voltage",
                "addr": ConfigMap.addr_vt_primary_ll_voltage,
                "type": "uint32",
                "access_addr": ConfigMap.addr_measurement_setup_access,
                "values": [1900],
                "touch_nav": {
                    "main_menu": ConfigTouch.touch_main_menu_1.value,
                    "side_menu": ConfigTouch.touch_side_menu_1.value,
                    "data_view": ConfigTouch.touch_data_view_3.value,
                    "password": False,
                },
                "input_type": "number",
                "key_type": None,
                "display_map": None,
            },
            # ----- 오른쪽 2행 [620,280] -----
            {
                "name": "VT Secondary LL Voltage",
                "addr": ConfigMap.addr_vt_secondary_ll_voltage,
                "type": "uint16",
                "access_addr": ConfigMap.addr_measurement_setup_access,
                "values": [220],
                "touch_nav": {
                    "main_menu": ConfigTouch.touch_main_menu_1.value,
                    "side_menu": ConfigTouch.touch_side_menu_1.value,
                    "data_view": ConfigTouch.touch_data_view_4.value,
                    "password": False,
                },
                "input_type": "number",
                "key_type": None,
                "display_map": None,
            },
            # ----- 왼쪽 3행 [320,360] -----
            {
                "name": "Reference Voltage",
                "addr": ConfigMap.addr_reference_voltage,
                "type": "uint32",
                "access_addr": ConfigMap.addr_measurement_setup_access,
                "values": [1900],
                "touch_nav": {
                    "main_menu": ConfigTouch.touch_main_menu_1.value,
                    "side_menu": ConfigTouch.touch_side_menu_1.value,
                    "data_view": ConfigTouch.touch_data_view_5.value,
                    "password": False,
                },
                "input_type": "number",
                "key_type": "ref",
                "display_map": None,
            },
            # Reference Voltage Mode — 화면에 별도 셀 없음 (Reference Voltage 셀의 popup에 통합된 것으로 보임).
            # 동작 확인 후 별도 처리 방식 결정. 일단 비활성화.
            # ----- 왼쪽 4행 [320,430] -----
            {
                "name": "Rotating Sequence",
                "addr": ConfigMap.addr_rotating_sequence,
                "type": "uint16",
                "access_addr": ConfigMap.addr_measurement_setup_access,
                "values": [1, 2],
                "touch_nav": {
                    "main_menu": ConfigTouch.touch_main_menu_1.value,
                    "side_menu": ConfigTouch.touch_side_menu_1.value,
                    "data_view": ConfigTouch.touch_data_view_7.value,
                    "password": False,
                },
                "input_type": "popup",
                "popup_options": {
                    1: ConfigTouch.touch_btn_popup_1.value,
                    2: ConfigTouch.touch_btn_popup_2.value,
                },
                "display_map": {0: "Auto", 1: "Positive", 2: "Negative"},
            },
        ],
        "Current": [],
        "Power": [],
        "Demand": [],
    },
}
