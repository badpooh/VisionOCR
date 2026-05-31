# -*- coding: utf-8 -*-
# A3700N 제품 전용 Modbus 주소 맵 (설정 영역).
#
# 참조: uploads/Accura 3700N Modbus Map.xlsx (Setup + Event Setup 섹션)
# 비교: config_map_a7300.py (기존 A7300 원본)
#
# 설계 원칙
#   1) A7300 과 기능이 동일한 항목은 같은 이름(addr_*)을 유지한다.
#      - func_modbus.py 등에서 ConfigMap 참조 코드를 그대로 재사용할 수 있도록.
#   2) A3700N 에서 완전히 신규인 필드는 본 파일 하단의 "A3700N 신규" 섹션에 추가한다.
#   3) A7300 에는 있으나 A3700N 설정 영역에 없는 필드는 주석으로 표시한다.
#      (예: wiring/VT/CT 등 Measurement Setup 6000 번대는 A3700N 에서 보이지 않음)
#
# 사용 방법
#   from config.config_product import get_map_module
#   cfg_map = get_map_module("A3700N").ConfigMap
#   self.setup_client.write_register(cfg_map.addr_setup_lock.value[0], 2300)

from enum import Enum


class ConfigMap(Enum):

    # ============================================================
    # Lock
    # ============================================================
    addr_setup_lock = (2901, 1)          # A7300: 2900 → +1
    addr_control_lock = (2902, 1)        # A7300: 2901 → +1

    # ============================================================
    # System - Summer Time Setup (A3700N 3001~3011)
    # ============================================================
    addr_summer_time_setup_access = (3001, 1)  # A7300: 3000
    addr_summer_time = (3002, 1)         # A7300: 3001
    addr_start_month = (3003, 1)         # 동일
    addr_start_nth_weekday = (3004, 1)
    addr_start_weekday = (3005, 1)
    addr_start_minute = (3006, 1)
    addr_end_month = (3007, 1)
    addr_end_nth_weekday = (3008, 1)
    addr_end_weekday = (3009, 1)
    addr_end_minute = (3010, 1)
    addr_summer_time_offset = (3011, 1)  # A7300: 3002 → 블록 마지막으로 이동

    # ============================================================
    # System - Locale Setup (A3700N 3021~3028)
    # ============================================================
    addr_locale_setup_access = (3021, 1)  # A7300: 3020
    addr_timezone_offset = (3022, 1)     # A7300: 3021
    addr_temperature_unit = (3023, 1)    # A7300: 3022
    addr_energy_unit = (3024, 1)         # A7300: 3023
    # A7300 의 addr_date_display_format(3024) 은 A3700N 설정에 없음.
    # A3700N 신규: Display measured data unit, Modbus connection/access log
    addr_display_measured_data_unit = (3025, 1)   # A3700N 신규
    addr_modbus_connection_log = (3026, 1)        # A3700N 신규
    addr_modbus_access_log = (3027, 1)            # A3700N 신규

    # ============================================================
    # System - NTP Setup (A3700N 3041~3046)
    # ============================================================
    addr_ntp_setup_access = (3041, 1)  # A7300: 3040
    addr_ntp_ip = (3042, 2)              # A7300: 3041 (UINT8x4)
    addr_sync_mode = (3044, 1)           # A7300: 3043
    addr_sync_period = (3045, 1)         # A7300: 3044
    addr_sync_max_drift = (3046, 1)      # A7300: 3045

    # ============================================================
    # System - System Time Setup (A3700N 3061~3065)
    # ============================================================
    addr_system_time_setup_access = (3060, 1)  # A7300: 3060
    addr_system_time_sec = (3061, 2)     # A7300: 3061 (UINT32)
    addr_system_time_usec = (3063, 2)    # A7300: 3063 (UINT32)

    # ============================================================
    # System - Description Setup (A3700N 3301~3335)
    # A3700N 신규: Device name / Location / Description (CHAR30)
    # ============================================================
    addr_description_setup_access = (3301, 1)  # A7300: 3300
    addr_device_name = (3302, 15)                # A3700N 신규 (CHAR30)
    addr_location = (3317, 15)                   # A3700N 신규 (CHAR30)
    addr_installation_year = (3332, 1)           # A7300: 3331
    addr_installation_month = (3333, 1)          # A7300: 3332
    addr_installation_day = (3334, 1)            # A7300: 3333
    addr_description = (3335, 15)                # A3700N 신규 (CHAR30)

    # ============================================================
    # System - CB Setup  (A3700N 신규, A7300에는 없음)
    # ============================================================
    addr_cb_setup_access = (3361, 1)
    addr_cb_on_di_id = (3362, 1)
    addr_cb_on_di_channel = (3363, 1)
    addr_cb_on_di_type = (3364, 1)
    addr_cb_on_di_lamp_color = (3365, 1)
    addr_cb_off_di_id = (3366, 1)
    addr_cb_off_di_channel = (3367, 1)
    addr_cb_off_di_type = (3368, 1)
    addr_cb_off_di_lamp_color = (3369, 1)

    # ============================================================
    # System - Remote Control Lock Mode
    # ============================================================
    addr_remote_control_lock_mode_access = (3401, 1)  # A7300: 3400
    addr_remote_control_lock_mode = (3402, 1)                             # A7300: 3401

    # ============================================================
    # Network - Ethernet Setup  (A3700N 3601~3606)
    # (A7300 에서는 DHCP 블록 등에 흩어져 있음)
    # ============================================================
    addr_ethernet_setup_access = (3601, 1)
    addr_eth_ip_address = (3602, 2)      # UINT8 x 4
    addr_eth_subnet_mask = (3604, 1)
    addr_eth_gateway = (3605, 2)         # UINT8 x 4

    # ============================================================
    # Network - Modbus Timeout Setup
    # ============================================================
    addr_modbus_timeout_setup_access = (3621, 1)  # A7300: 3620
    addr_modbus_timeout = (3622, 1)                                   # A7300: 3621

    # ============================================================
    # Network - RSTP Setup  (A3700N 3641~3661, 대폭 확장)
    # ============================================================
    addr_rstp_setup_access = (3641, 1)   # A7300: 3640
    addr_rstp = (3642, 1)                                    # A7300: 3641
    # 이하는 전부 A3700N 신규
    addr_rstp_bridge_priority = (3643, 1)
    addr_rstp_bridge_max_age = (3644, 1)
    addr_rstp_bridge_hello_time = (3645, 1)
    addr_rstp_bridge_forward_delay = (3646, 1)
    addr_rstp_bridge_aging_value = (3647, 1)
    addr_rstp_bridge_detection_time = (3648, 1)
    addr_rstp_transition_to_forward_time = (3649, 1)
    addr_rstp_tc_transmission_time = (3650, 1)
    addr_rstp_recent_backup_delay_time = (3651, 1)
    addr_rstp_tx_hold_count = (3652, 1)
    addr_rstp_broadcast_intensive_interval = (3653, 1)
    addr_rstp_broadcast_max_period = (3654, 1)
    addr_rstp_connection_poll_period = (3655, 1)
    addr_rstp_send_broadcast_enabled = (3656, 1)
    addr_rstp_root_port_monitoring_enabled = (3657, 1)
    addr_rstp_send_tc_enabled = (3658, 1)
    addr_rstp_flush_mac_enabled = (3659, 1)
    addr_rstp_erase_aged_received_info = (3660, 1)
    addr_rstp_allow_edge_port = (3661, 1)

    # ============================================================
    # Network - Storm Control Setup (A3700N 3681~3689, 확장)
    # ============================================================
    addr_storm_control_setup_access = (3681, 1)  # A7300: 3680
    addr_storm_control = (3682, 1)                                   # A7300: 3681
    # 이하는 A3700N 신규
    addr_storm_fec_detect_time_msec = (3683, 1)
    addr_storm_fec_detect_count = (3684, 2)             # INT32
    addr_storm_fec_max_contiguous_rx_time_msec = (3686, 1)
    addr_storm_fec_allowed_violation_count = (3687, 1)
    addr_storm_fec_allowed_rx_per_100msec = (3688, 2)   # INT32

    # ============================================================
    # Network - RS-485 Setup
    # ============================================================
    addr_rs485_setup_access = (3701, 1)  # A7300: 3700
    addr_device_address = (3702, 1)                          # A7300: 3701
    addr_bit_rate = (3703, 1)                                # A7300: 3702
    addr_parity = (3704, 1)                                  # A7300: 3703
    addr_stop_bit = (3705, 1)                                # A7300: 3704

    # NOTE: A7300 의 addr_rs485_map (3630~3631) 은 A3700N 설정에 해당 블록 없음.

    # ============================================================
    # Network - DHCP Setup (A3700N 에서는 실제 받은 IP/Subnet/Gateway 를 R 노출)
    # ============================================================
    addr_dhcp_setup_access = (3721, 1)  # A7300: 3720
    addr_dhcp = (3722, 1)                                   # A7300: 3721
    addr_dhcp_ip_address = (3723, 2)                        # A3700N 신규 (R)
    addr_dhcp_subnet_mask = (3725, 1)                       # A3700N 신규 (R)
    addr_dhcp_gateway = (3726, 2)                           # A3700N 신규 (R)

    # ============================================================
    # Measurement - Aggregation Setup  (A3700N 3801~3822)
    # A7300 은 addr_aggregation_selection(14900, 1) 단일 레지스터만 존재.
    # A3700N 은 프로파일 11~15 를 enable/interval/offset 으로 세부 설정.
    # ============================================================
    addr_aggregation_setup_access = (3801, 1)
    addr_default_aggregation_selection = (3802, 1)
    addr_aggregation_11_enable = (3803, 1)
    addr_aggregation_11_interval = (3804, 2)   # UINT32
    addr_aggregation_11_offset = (3806, 1)
    addr_aggregation_12_enable = (3807, 1)
    addr_aggregation_12_interval = (3808, 2)
    addr_aggregation_12_offset = (3810, 1)
    addr_aggregation_13_enable = (3811, 1)
    addr_aggregation_13_interval = (3812, 2)
    addr_aggregation_13_offset = (3814, 1)
    addr_aggregation_14_enable = (3815, 1)
    addr_aggregation_14_interval = (3816, 2)
    addr_aggregation_14_offset = (3818, 1)
    addr_aggregation_15_enable = (3819, 1)
    addr_aggregation_15_interval = (3820, 2)
    addr_aggregation_15_offset = (3822, 1)

    # A7300 과의 호환성을 위해 동일 이름도 하나 유지
    # (14900 대신 A3700N 의 "default aggregation selection" 에 매핑)
    addr_aggregation_selection = {'address': 3802, 'count': 1}

    # ============================================================
    # Measurement - V0-I0 mode Setup  (A3700N 신규)
    # ============================================================
    addr_v0_i0_mode_setup_access = (3841, 1)
    addr_v0_i0_mode = (3842, 1)

    # ============================================================
    # UI - LED Setup  (A3700N 신규)
    # ============================================================
    addr_led_setup_access = (3921, 1)
    addr_led_ethernet_period = (3922, 1)
    addr_led_ethernet_on_time = (3923, 1)
    addr_led_event_period = (3924, 1)
    addr_led_event_on_time = (3925, 1)
    addr_led_rs485_period = (3926, 1)
    addr_led_rs485_on_time = (3927, 1)
    addr_led_event_hold_time = (3928, 1)

    # ============================================================
    # UI - LCD/Buzzer Setup (A3700N 3941~3944, A7300: 3800~3803)
    # ============================================================
    addr_lcd_buzzer_setup_access = (3941, 1)  # A7300: 3800
    addr_lcd_backlight_timeout = (3942, 1)                        # A7300: 3801
    addr_lcd_backlight_low_level = (3943, 1)                      # A7300: 3802
    addr_buzzer_for_button = (3944, 1)                            # A7300: 3803

    # ============================================================
    # Test Mode Setup (A3700N 4001~4002)
    # A7300 은 addr_meter_test_mode(4000) 이 존재. A3700N 에는 해당 레지스터 없음.
    # ============================================================
    addr_meter_demo_mode_timeout_setup_access = (4001, 1)   # A7300: 4001 (access)
    addr_meter_demo_mode_timeout = (4002, 1)                # A7300: 4002

    # ============================================================
    # Event Setup - Dip (A3700N 5101~5108, A7300: 5100~5103)
    # A3700N 에서는 DO 연동 필드 추가
    # ============================================================
    addr_dip_setup_access = (5101, 1)    # A7300: 5100
    addr_dip = (5102, 1)                 # A7300: 5101
    addr_dip_threshold = (5103, 1)       # A7300: 5102
    addr_dip_hysteresis = (5104, 1)      # A7300: 5103
    addr_dip_do_id_channel = (5106, 1)   # A3700N 신규
    addr_dip_do_module_type = (5107, 1)  # A3700N 신규

    # Event Setup - 3-Phase Dip (A3700N 5111~5116)
    addr_3phase_dip_setup_access = (5111, 1)   # A7300: 5110
    addr_3phase_dip = (5112, 1)                # A7300: 5111
    addr_3phase_interruption_ratio = (5113, 1)        # A3700N 신규
    addr_3phase_interruption_delay_time = (5114, 1)   # A3700N 신규
    addr_3phase_dip_do_id_channel = (5115, 1)         # A3700N 신규
    addr_3phase_dip_do_module_type = (5116, 1)        # A3700N 신규

    # Event Setup - Swell (A3700N 5121~5127)
    addr_swell_setup_access = (5121, 1)   # A7300: 5120
    addr_swell = (5122, 1)                # A7300: 5121
    addr_swell_threshold = (5123, 1)      # A7300: 5122
    addr_swell_hysteresis = (5124, 1)     # A7300: 5123
    addr_swell_do_id_channel = (5126, 1)  # A3700N 신규
    addr_swell_do_module_type = (5127, 1) # A3700N 신규

    # Event Setup - Fuse Fail (A3700N 신규, 5141~5144)
    addr_fuse_fail_setup_access = (5141, 1)
    addr_fuse_fail = (5142, 1)
    addr_fuse_fail_do_id_channel = (5143, 1)
    addr_fuse_fail_do_module_type = (5144, 1)

    # Event Setup - Phase Open (A3700N 신규, 5161~5164)
    addr_phase_open_setup_access = (5161, 1)
    addr_phase_open = (5162, 1)
    addr_phase_open_do_id_channel = (5163, 1)
    addr_phase_open_do_module_type = (5164, 1)

    # Event Setup - Custom Event (A3700N 신규, 5201~ , 15 채널)
    addr_custom_event_channel = (5201, 1)
    addr_custom_event_setup_access = (5202, 1)
    addr_custom_event_source = (5203, 1)
    addr_custom_event_module_id = (5204, 1)
    addr_custom_event_module_type = (5205, 1)
    addr_custom_event_trigger = (5206, 1)
    addr_custom_event_data_type = (5207, 1)
    addr_custom_event_data_offset = (5208, 1)
    addr_custom_event_time_delay = (5209, 1)
    addr_custom_event_threshold = (5211, 2)   # FLOAT32

    # Event Setup - SEMI F47-0706 (A3700N: 5301~, A7300: 5160~)
    # A3700N 은 세부 필드가 많아 base access 만 매핑하고 나머지는 TODO
    addr_semi_event_setup_access = (5301, 1)   # A7300: 5160
    addr_semi = (5302, 1)                      # A7300: 5161
    # TODO(A3700N): SEMI Class A/B/C threshold 등 세부 필드 추가

    # Event Setup - ITIC (A3700N: 5401~, A7300: 5190~)
    addr_itic_event_setup_access = (5401, 1)   # A7300: 5190
    addr_itic = (5402, 1)                      # A7300: 5191
    # TODO(A3700N): ITIC curve 세부 threshold 필드 추가

    # Event Setup - IEC 61000-4-11/34 Class 3 (A3700N: 5501~, A7300: 5220~)
    addr_iec_event_setup_access = (5501, 1)    # A7300: 5220
    addr_iec = (5502, 1)                       # A7300: 5221
    # TODO(A3700N): IEC Class 3 세부 threshold 필드 추가

    # Event Setup - Blackout (A3700N 신규, 5601~)
    addr_blackout_setup_access = (5601, 1)
    addr_blackout = (5602, 1)

    # Event Setup - Current RMS (A3700N 신규, 5651~)
    addr_current_rms_setup_access = (5651, 1)
    addr_current_rms = (5652, 1)

    # Event Setup - Event Save Mode (A3700N 신규, 5701~)
    addr_event_save_mode_setup_access = (5701, 1)
    addr_event_save_mode = (5702, 1)

    # Event Setup - Reference Voltage Selection (A3700N 신규, 5751~)
    addr_reference_voltage_selection_setup_access = (5751, 1)
    addr_reference_voltage_selection = (5752, 1)

    # ============================================================
    # Control — A3700N 사양서 8001~8051 (pymodbus -1 적용).
    # A7300 와 register block 자체가 다름 — A7300: 12000번대.
    # ============================================================
    addr_reset_demand            = (8000, 1)   # spec 8001 Demand Reset
    addr_reset_demand_peak       = (8001, 1)   # spec 8002 Peak Demand
    addr_reset_max_min           = (8002, 1)   # spec 8003 Max/Min Reset
    addr_reset_energy            = (8003, 1)   # spec 8004 Energy Reset
    addr_reset_pq_event          = (8004, 1)   # spec 8005 PQ Event Reset
    addr_reset_system_event      = (8005, 1)   # spec 8006 System Event Reset
    addr_reset_measurement_event = (8006, 1)   # spec 8007 Measurement Event Reset
    addr_demand_sync             = (8007, 1)   # spec 8008 Demand Sync Setter
    addr_reset_di_fault          = (8008, 1)   # spec 8009 DI Fault Record Reset
    addr_aggregation_clear       = (8030, 1)   # spec 8031 Aggregation Clear
    addr_test_mode_control       = (8050, 1)   # spec 8051 Test Mode Control

    # ============================================================
    # Module Setup (A3700N 전용 구조 — 사양값 -1)
    # ------------------------------------------------------------
    # A3700N 은 모듈 기반 구조라 A7300 과 다르다:
    #   1. addr_module_id 에 0(MCU) 쓰기
    #   2. addr_measurement_setup_access read (fetch)
    #   3. 6002 ~ 에 setup 값 쓰기
    #   4. addr_measurement_setup_access write 0 (MCU 타입으로 commit)
    # A7300 과 같은 이름은 주소만 +1 shift 됨.
    # ============================================================
    addr_module_id = (6000, 1)                                    # 사양 6001 (Module ID)
    addr_measurement_setup_access = {'address': 6001, 'count': 1} # 사양 6002 (Module setup access)
    # MCU offset 0~39 (사양 6003 ~ 6042, Python -1)
    addr_wiring = (6002, 1)                                       # 사양 6003 offset 0
    # offset 1: RESERVED
    addr_reference_voltage = (6004, 2)                            # 사양 6005 offset 2 (UINT32)
    addr_pt_primary_voltage = (6006, 2)                           # 사양 6007 offset 4 (UINT32)
    # A7300 호환 alias (이름은 VT지만 실제로는 PT)
    addr_vt_primary_ll_voltage = addr_pt_primary_voltage
    addr_pt_secondary_voltage = (6008, 1)                         # 사양 6009 offset 6
    addr_vt_secondary_ll_voltage = addr_pt_secondary_voltage
    addr_min_measured_secondary_voltage = (6009, 1)               # 사양 6010 offset 7
    addr_min_measured_secondary_ln_voltage = addr_min_measured_secondary_voltage
    addr_reference_voltage_mode = (6010, 1)                       # 사양 6011 offset 8
    addr_voltage_phase_selection = (6011, 1)                      # 사양 6012 offset 9 (신규)
    addr_a_voltage_polarity = (6012, 1)                           # 사양 6013 offset 10 (신규)
    addr_b_voltage_polarity = (6013, 1)                           # 사양 6014 offset 11 (신규)
    addr_c_voltage_polarity = (6014, 1)                           # 사양 6015 offset 12 (신규)
    # offset 13: RESERVED
    addr_reference_current = (6016, 2)                            # 사양 6017 offset 14 (UINT32)
    addr_ct_primary_current = (6018, 2)                           # 사양 6019 offset 16 (UINT32)
    addr_ct_secondary_current = (6020, 1)                         # 사양 6021 offset 18
    addr_min_measured_current = (6021, 1)                         # 사양 6022 offset 19
    addr_nominal_tdd_current = (6022, 2)                          # 사양 6023 offset 20 (UINT32)
    addr_tdd_reference = (6024, 1)                                # 사양 6025 offset 22
    addr_current_phase_selection = (6025, 1)                      # 사양 6026 offset 23 (신규)
    addr_a_current_direction = (6026, 1)                          # 사양 6027 offset 24 (신규)
    addr_b_current_direction = (6027, 1)                          # 사양 6028 offset 25 (신규)
    addr_c_current_direction = (6028, 1)                          # 사양 6029 offset 26 (신규)
    addr_demand_sync_mode = (6029, 1)                             # 사양 6030 offset 27
    addr_num_of_sub_interval = (6030, 1)                          # 사양 6031 offset 28
    addr_sub_interval_time = (6031, 1)                            # 사양 6032 offset 29
    addr_thermal_response_index = (6032, 1)                       # 사양 6033 offset 30
    addr_demand_power_type = (6033, 1)                            # 사양 6034 offset 31
    addr_phase_power_calculation = (6034, 1)                      # 사양 6035 offset 32
    addr_total_power_calculation = (6035, 1)                      # 사양 6036 offset 33
    addr_pf_value_at_no_load = (6036, 1)                          # 사양 6037 offset 34
    addr_pf_sign = (6037, 1)                                      # 사양 6038 offset 35
    addr_reactive_power_sign = (6038, 1)                          # 사양 6039 offset 36
    addr_default_frequency = (6039, 1)                            # 사양 6040 offset 37 (신규, default 0=60Hz)
    addr_max_harmonic_order = (6040, 1)                           # 사양 6041 offset 38 (신규, 50 고정)
    addr_rotating_sequence = (6041, 1)                            # 사양 6042 offset 39
    addr_sliding_reference_voltage_setup_access = {'address': 5520, 'count': 1}
    addr_sliding_reference_voltage_type = (5521, 1)  # default 0

    # ============================================================
    # A3700N 에 없는 A7300 항목 (Sliding Reference Voltage 등)
    # ------------------------------------------------------------
    # A7300 에는 6050~ 에 sliding_reference_voltage_setup_access 가 있으나
    # A3700N 의 Module Setup 영역(6003~6042)에는 보이지 않음. 매핑 안 함.
    # 해�