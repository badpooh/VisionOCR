# -*- coding: utf-8 -*-
# A7300 제품 전용 ROI 설정.
# - 이 파일은 A7300 화면 기준으로 작성된 원본이다.
# - A3700N / A2700 은 이 파일을 참조해서 필요한 좌표/모드버스 주소만 덮어쓴다.
# - 새 제품을 추가하면 config_product.get_roi_module() 로더에도 등록할 것.

from enum import Enum

class ConfigROI(Enum):
    title_view = ["RMS Voltage L-L L-N Min Max", "AB", "BC", "CA", "Average"]
    a_ab = "meas_a_phase_name"
    a_time_stamp = "meas_a_time_stamp"
    a_meas = "meas_a_measurement_value"
    b_bc = "meas_b_phase_name"
    b_time_stamp = "meas_b_time_stamp"
    b_meas = "meas_b_measurement_value"
    c_ca = "meas_c_phase_name"
    c_time_stamp = "meas_c_time_stamp"
    c_meas = "meas_c_measurement_value"
    aver = "meas_aver_phase_name"
    aver_time_stamp = "meas_aver_time_stamp"
    aver_meas = "meas_aver_measurement_value"
    curr_per_a = "meas_curr_percent_a"
    curr_per_b = "meas_curr_percent_b"
    curr_per_c = "meas_curr_percent_c"
    curr_per_aver = "meas_curr_percent_aver"
    
    phasor_img_cut = "phasor_img_cut"
    phasor_title = "phasor_title"
    phasor_title_2 = "phasor_title_2"
    phasor_view_2 = "phasor_view_2"
    phasor_vl_vn = "phasor_vl_vn"
    phasor_voltage = "phasor_voltage"
    phasor_a_c_vol = "phasor_a_c_vol"
    phasor_a_meas = "phasor_a_meas"
    phasor_a_angle = "phasor_a_angle"
    phasor_b_meas = "phasor_b_meas"
    phasor_b_angle = "phasor_b_angle"
    phasor_c_meas = "phasor_c_meas"
    phasor_c_angle = "phasor_c_angle"
    phasor_a_c_angle_vol = "phasor_a_c_angle_vol"
    phasor_current = "phasor_current"
    phasor_a_c_cur = "phasor_a_c_cur"
    phasor_a_meas_cur = "phasor_a_meas_cur"
    phasor_a_angle_cur = "phasor_a_angle_cur"
    phasor_b_meas_cur = "phasor_b_meas_cur"
    phasor_b_angle_cur = "phasor_b_angle_cur"
    phasor_c_meas_cur = "phasor_c_meas_cur"
    phasor_c_angle_cur = "phasor_c_angle_cur"
    phasor_a_c_angle_cur = "phasor_a_c_angle_cur"
    
    waveform_title = "waveform_title"
    waveform_all_img_cut = "waveform_img_cut"
    waveform_graph_img_cut = "waveform_graph_img_cut"
    
    harmonics_img_cut = "harmonics_img_cut"
    harmonics_title = "harmonics_title"
    harmonics_sub_title_1 = "harmonics_sub_title_1"
    harmonics_sub_title_2 = "harmonics_sub_title_2"
    harmonics_sub_title_3 = "harmonics_sub_title_3"
    harmonics_graph_img_cut = "harmonics_graph_img_cut"
    harmonics_chart_img_cut = "harmonics_graph_with_bar_img_cut"
    harmonics_graph_a = "harmonics_graph_a"
    harmonics_graph_b = "harmonics_graph_b"
    harmonics_graph_c = "harmonics_graph_c"
    harmonics_text_title = "harmonics_text_title"
    harmonics_text_img = "harmonics_text_image"
    harmonics_text_number_title_1 = ["0", "1", "2", "3", "4", "5", "6", "7", "8"]
    harmonics_text_number_meas_1 = "measurement result"
    harmonics_text_chart_img_cut_3 = ["6, 0.000, 15, 0.000, 24, 0.000, 33, 0.000, 42, 0.000, 7, 0.000, 16, 0.000, 25, 0.000, 34, 0.000, 43, 0.000, 8, 0.000, 17, 0.000, 26, 0.000, 35, 0.000, 44, 0.000"]
    harmonics_text_sub_title = "harmonics_text_sub_title"
    harmonics_text_sub_abc = "harmonics_text_sub_a"
    harmonics_thd_a = "harmonics_thd_a"
    harmonics_thd_b = "harmonics_thd_b"
    harmonics_thd_c = "harmonics_thd_c"
    harmonics_fund_a = "harmonics_fund_a"
    harmonics_fund_b = "harmonics_fund_b"
    harmonics_fund_c = "harmonics_fund_c"

    ### for meter setup test ###
    s_wiring_1 = ['Wiring']
    s_wiring_2 = ('Wiring', {'Wye': 0, 'Delta': 1})
    s_min_meas_sec_ln_vol_1 = ['Min. Meas. Secondary L-N Volt. [V]']
    s_min_meas_sec_ln_vol_2 = ('Min. Meas. Secondary L-N Volt. [V]', ['0', '10'])
    s_vt_primary_ll_vol_1 = ['VT Primary L-L Voltage [V]']
    s_vt_primary_ll_vol_2 = ('VT Primary L-L Voltage [V]', ['50.0', '999999.0'])
    s_vt_secondary_ll_vol_1 = ['VT Secondary L-L Voltage [V]']
    s_vt_secondary_ll_vol_2 = ('VT Secondary L-L Voltage [V]', ['50.0', '220.0'])
    s_primary_reference_vol_1 = ['Primary Reference Voltage [V]']
    s_primary_reference_vol_2 = ('Primary Reference Voltage [V]', {'Line-to-Line': 0, 'Line-to-Neutral': 1}, ['50.0', '999999.0'])
    s_primary_reference_vol_3 = ('LL_LN_Pri Ref Vol', {'Line-to-Line, 190.0': 0, 'Line-to-Neutral, 190.0': 1})
    s_primary_reference_vol_4 = ('Range_Pri Ref Vol', ['Line-to-Line, 50.0', 'Line-to-Line, 999999.0'])
    s_sliding_reference_vol_1 = ['Sliding Reference Voltage']
    s_sliding_reference_vol_2 = ('Sliding Reference Voltage', {'Disable': 0, 'Enable': 1})
    s_rotation_sequence_1 = ['Rotating Sequence']
    s_rotation_sequence_2 = ('Rotating Sequence', {'Positive': 1, 'Negative': 2})
    # current
    s_ct_primary_curr_1 = ['CT Primary Current [A]']
    s_ct_primary_curr_2 = ('CT Primary Current [A]', ['5', '99999'])
    s_ct_secondary_curr_1 = ['CT Secondary Current [A]']
    s_ct_secondary_curr_2 = ('CT Secondary Current [A]', ['5', '10'])
    s_reference_curr_1 = ['Reference Current [A]']
    s_reference_curr_2 = ('Reference Current [A]', ['5', '99999'])
    s_min_meas_curr_1 = ['Min. Measured Current [mA]']
    s_min_meas_curr_2 = ('Min. Measured Current [mA]', ['0', '100'])
    s_tdd_reference_selection_1 = ['TDD Reference Selection']
    s_tdd_reference_selection_2 = ('TDD Reference Selection', {'TDD Nominal Current': 0, 'Peak Demand Current': 1})
    s_tdd_nominal_curr_1 = ['TDD Nominal Current [A]']
    s_tdd_nominal_curr_2 = ('TDD Nominal Current [A]', ['Reference Current', '1', '99999'])
    # demand
    s_sub_interval_time_1 = ['Subinterval Time [min]']
    s_sub_interval_time_2 = ('Subinterval Time [min]', ['1', '60'])
    s_number_of_sub_intervals_1 = ['Number of Subintervals']
    s_number_of_sub_intervals_2 = ('Number of Subintervals', ['1', '12'])
    s_demand_power_type_1 = ['Power Type']
    s_demand_power_type_2 = ('Power Type', {'Received': 0, 'Net': 1})
    s_demand_sync_mode_1 = ('demand', ['Sync Mode'])
    s_demand_sync_mode_2 = ('Sync Mode', {'Hourly Auto Sync': 0, 'Manual Sync': 1})
    s_thermal_response_index_1 = ['Thermal Response Index [%]']
    s_thermal_response_index_2 = ('Thermal Response Index [%]', ['0', '100'])
    # power
    s_phase_power_calculation_1 = ['Phase Power Calculation']
    s_phase_power_calculation_2 = ('Phase Power Calculation', {'Fundamental': 0, 'RMS': 1})
    s_total_power_calculation_1 = ['Total Power Calculation']
    s_total_power_calculation_2 = ('Total Power Calculation', {'Vector Sum': 0, 'Arithmetic Sum': 1})
    s_pf_sign_1 = ['PF Sign']
    s_pf_sign_2 = ('PF Sign', {'Unsigned': 0, 'Signed': 1})
    s_pf_value_at_noload_1 = ['PF Value at No Load']
    s_pf_value_at_noload_2 = ('PF Value at No Load', {'PF = 0': 0, 'PF = 1': 1})
    s_reactive_power_sign_1 = ['Reactive Power Sign']
    s_reactive_power_sign_2 = ('Reactive Power Sign', {'Unsigned': 0, 'Signed': 1})

    # event>dip
    s_dip_trigger_1 = ('dip', ['Trigger'])
    s_dip_trigger_2 = ('dip', ('Trigger', {'Disable': 0, 'Enable': 1}))
    s_dip_threshold_1 = ('dip', ['Threshold [%]'])
    s_dip_threshold_2 = ('dip', ('Threshold [%]', ['1.0', '99.0']))
    s_dip_hysteresis_1 = ('dip', ['Hysteresis [%]'])
    s_dip_hysteresis_2 = ('dip', ('Hysteresis [%]', ['1.0', '99.0']))
    s_dip_3phase_dip_1 = ['3-Phase Dip']
    s_dip_3phase_dip_2 = ('3-Phase Dip', {'Disable': 0, 'Enable': 1})
    # swell
    s_swell_trigger_1 = ('swell', ['Trigger'])
    s_swell_trigger_2 = ('swell', ('Trigger', {'Disable': 0, 'Enable': 1}))
    s_swell_threshold_1 = ('swell', ['Threshold [%]'])
    s_swell_threshold_2 = ('swell', ('Threshold [%]', ['101.0', '999.0']))
    s_swell_hysteresis_1 = ('swell', ['Hysteresis [%]'])
    s_swell_hysteresis_2 = ('swell', ('Hysteresis [%]', ['1.0', '99.0']))
    # pq curve
    s_pq_curve_semi_1 = ['SEMI F47-0706']
    s_pq_curve_semi_2 = ('SEMI F47-0706', {'Disable': 0, 'Enable': 1})
    s_pq_curve_iec_1 = ['IEC 61000-4-11/34 Class 3']
    s_pq_curve_iec_2 = ('IEC 61000-4-11/34 Class 3', {'Disable': 0, 'Enable': 1})
    s_pq_curve_itic_1 = ['ITIC']
    s_pq_curve_itic_2 = ('ITIC', {'Disable': 0, 'Enable': 1})

    # network>ethernet
    s_dhcp_1 = ['DHCP']
    s_dhcp_2 = ('DHCP', {'Disable': 0, 'Enable': 1})

    # rs-485
    s_device_address_1 = ['Device Address']
    s_device_address_2 = ('Device Address', ['0', '247'])
    s_bit_rate_1 = ['Bit Rate']
    s_bit_rate_2 = ('Bit Rate', {'1200': 0, '2400': 1, '4800': 2, '9600': 3, '19200': 4, '38400': 5, '57600': 6, '115200': 7})
    s_parity_1 = ['Parity']
    s_parity_2 = ('Parity', {'None': 0, 'Odd': 1, 'Even': 2})
    s_stop_bit_1 = ['Stop Bit']
    s_stop_bit_2 = ('Stop Bit', {'1': 0, '2': 1})
    # advanced
    s_modbus_timeout_1 = ['Modbus TCP Timeout [sec]']
    s_modbus_timeout_2 = ('Modbus TCP Timeout [sec]', ['5', '600'])
    s_rstp_1 = ['RSTP']
    s_rstp_2 = ('RSTP', {'Disable': 0, 'Enable': 1})
    s_storm_control_1 = ['Storm Control']
    s_storm_control_2 = ('Storm Control', {'Disable': 0, 'Enable': 1})
    s_rs485_map_1 = ['RS-485 Map']
    s_rs485_map_2 = ('RS-485 Map', {'Accura 7300': 0, 'Accura 7500': 1})
    s_remote_control_lock_mode_1 = ['Remote Control Lock Mode'] # 오타 확인 Mdoe -> Mode
    s_remote_control_lock_mode_2 = ('Remote Control Lock Mode', {'Each Connection Lock': 0, 'Always Unlock': 1}) # 오타 수정 반영

    # control>data reset
    s_data_reset_demand = ['Demand']
    s_data_reset_peak_demand = ['Peak Demand']
    s_data_reset_max_min = ['Max/Min']
    s_data_reset_energy = ['Energy']
    s_data_reset_pq_event = ['PQ Event']
    # demand sync
    s_demand_sync = ['Demand Sync']
    s_test_mode_1 = ['Test Mode']
    s_test_mode_2 = ('Test Mode', {'Off': 0, 'Balance': 1, 'Unbalance': 2, 'Dip Short': 3, 'Dip Long': 4, 'Swell Short': 5, 'Swell Long': 6})
    s_test_mode_timeout_1 = ['Timeout [min]']
    s_test_mode_timeout_2 = ('Timeout [min]', ['Infinite', '1', '1440'])

    # system>description
    s_device_name = ['Device Name']
    s_user_defined_info = ['User-Defined Info']
    s_location = ['Location']
    s_installation_year_1 = ['Installation Year']
    s_installation_year_2 = ('Installation Year', ['1970', '9999'])
    s_installation_month_1 = ['Installation Month']
    s_installation_month_2 = ('Installation Month', ['1', '12'])
    s_installation_day_1 = ['Installation Day']
    s_installation_day_2 = ('Installation Day', ['1', '31'])
    # locale
    s_timezone_offset_1 = ['Timezone Offset [min]']
    s_timezone_offset_2 = ('Timezone Offset [min]', ['-720', '840'])
    s_temperature_unit_1 = ['Temperature Unit']
    s_temperature_unit_2 = ('Temperature Unit', {'Celsius': 0, 'Fahrenheit': 1})
    s_energy_unit_1 = ['Energy Unit']
    s_energy_unit_2 = ('Energy Unit', {'kWh': 0, 'Wh': 1})
    s_date_format_1 = ['Date Format']
    s_date_format_2 = ('Date Format', {'YYYY-MM-DD': 0, 'YYYY-DD-MM': 1, 'YYYY/DD/MM': 2, 'MM.DD.YYYY': 3, 
                                       'MM/DD/YYYY': 4, 'MM-DD-YYYY': 5, 'DD.MM.YYYY': 6, 'DD/MM/YYYY': 7, 'DD-MM-YYYY': 8 
                                       })
    # local time
    s_year_1 = ['Year']
    s_year_2 = ('Year', ['1970', '2037'])
    s_month_1 = ['Month']
    s_month_2 = ('Month', ['1', '12'])
    s_day_1 = ['Day']
    s_day_2 = ('Day', ['1', '31'])
    s_hour_1 = ['Hour']
    s_hour_2 = ('Hour', ['0', '23'])
    s_minute_1 = ['Minute']
    s_minute_2 = ('Minute', ['0', '59'])
    s_second_1 = ['Second']
    s_second_2 = ('Second', ['0', '59'])
    # summer time
    s_summer_time_mode_1 = ['Summer Time'] # 'Mode' 가 너무 일반적임, 'Summer Time Mode' 등 구체화 고려
    s_summer_time_mode_2 = ('Summer Time', {'Disable': 0, 'Enable': 1})
    s_summer_time_time_offset_1 = ['Time Offset [min]']
    s_summer_time_time_offset_2 = ('Time Offset [min]', ['0', '1439'])
    s_start_month_1 = ['Start Month']
    s_start_month_2 = ('Start Month', {'January': 1, 'February': 2, 'March': 3, 'April': 4, 'May': 5, 'June': 6,
                                        'July': 7, 'August': 8, 'September': 9, 'October': 10, 'November': 11, 'December': 12})
    s_start_nth_weekday_1 = ['Start Nth Weekday']
    s_start_nth_weekday_2 = ('Start Nth Weekday', {'1st': 1, '2nd': 2, '3rd': 3, '4th': 4, '5th': 5})
    s_start_weekday_1 = ['Start Weekday']
    s_start_weekday_2 = ('Start Weekday', {'Sunday': 0, 'Monday': 1, 'Tuesday': 2, 'Wednesday': 3, 'Thursday': 4,
                                            'Friday': 5, 'Saturday': 6})
    s_start_minute_1 = ['Start Minute']
    s_start_minute_2 = ('Start Minute', ['0', '1439'])
    s_end_month_1 = ['End Month']
    s_end_month_2 = ('End Month', {'January': 1, 'February': 2, 'March': 3, 'April': 4, 'May': 5, 'June': 6,
                                        'July': 7, 'August': 8, 'September': 9, 'October': 10, 'November': 11, 'December': 12})
    s_end_nth_weekday_1 = ['End Nth Weekday']
    s_end_nth_weekday_2 = ('End Nth Weekday', {'1st': 1, '2nd': 2, '3rd': 3, '4th': 4, '5th': 5})
    s_end_weekday_1 = ['End Weekday']
    s_end_weekday_2 = ('End Weekday', {'Sunday': 0, 'Monday': 1, 'Tuesday': 2, 'Wednesday': 3, 'Thursday': 4, 
                                       'Friday': 5, 'Saturday': 6})
    s_end_minute_1 = ['End Minute']
    s_end_minute_2 = ('End Minute', ['0', '1439'])

    # ntp
    # server ip address
    s_sync_mode_1 = ('ntp', ['Sync Mode'])
    s_sync_mode_2 = ('ntp', {'Disable': 0, 'Auto': 1, 'Periodic': 2})
    s_sync_period_1 = ['Sync Period [sec]']
    s_sync_period_2 = ('Sync Period [sec]', ['60', '999'])
    s_sync_max_drift_1 = ['Sync Max. Drift [ms]']
    s_sync_max_drift_2 = ('Sync Max. Drift [ms]', ['1', '1000'])
    # lcd & buzzer
    s_lcd_backlight_timeout_1 = ['LCD Backlight Timeout [sec]']
    s_lcd_backlight_timeout_2 = ('LCD Backlight Timeout [sec]', ['10', '999'])
    s_lcd_backlight_low_level_1 = ['LCD Backlight Low Level [%]']
    s_lcd_backlight_low_level_2 = ('LCD Backlight Low Level [%]', ['0', '30'])
    s_buzzer_for_button_1 = ['Buzzer for Button']
    s_buzzer_for_button_2 = ('Buzzer for Button', {'Disable': 0, 'Enable': 1}) 

    color_main_menu_vol = [10, 70, 10, 10, 67, 136, 255]
    color_main_menu_curr = [170, 70, 10, 10, 67, 136, 255]
    color_rms_vol_ll = [380, 140, 10, 10, 67, 136, 255]
    color_rms_vol_ln = [480, 140, 10, 10, 67, 136, 255]
    color_vol_thd_ll = [480, 140, 10, 10, 67, 136, 255]
    color_vol_thd_ln = [580, 140, 10, 10, 67, 136, 255]
    color_phasor_vll = [580, 200, 10, 10, 67, 136, 255]
    color_phasor_vln = [680, 200, 10, 10, 67, 136, 255]
    color_symm_thd_vol_ll = [480, 140, 10, 10, 67, 136, 255]
    color_symm_thd_vol_ln = [580, 140, 10, 10, 67, 136, 255]
    ### A상 버튼 눌러서 A상이 안보이는 지 확인 / 앞 4자리는 검사할 그래프 영역###
    ### 뒤 3자리는 RGB ###
    color_waveform_vol_a = [313, 253, 411, 203, 0, 0, 0]
    color_waveform_vol_b = [313, 253, 411, 203, 255, 29, 37]
    color_waveform_vol_c = [313, 253, 411, 203, 0, 0, 255]
    color_waveform_curr_a = [313, 253, 411, 203, 153, 153, 153]
    color_waveform_curr_b = [313, 253, 411, 203, 255, 180, 245]
    color_waveform_curr_c = [313, 253, 411, 203, 54, 175, 255]
    color_harmonics_vol_a = [313, 283, 455, 173, 0, 0, 0]
    color_harmonics_vol_b = [313, 283, 455, 173, 255, 29, 37]
    color_harmonics_vol_c = [313, 283, 455, 173, 0, 0, 255]
    color_harmonics_curr_a = [313, 283, 455, 173, 153, 153, 153]
    color_harmonics_curr_b = [313, 283, 455, 173, 255, 180, 245]
    color_harmonics_curr_c = [313, 283, 455, 173, 54, 175, 255]

    ### harmonics voltage, current 활성화 판별 ###
    ### 앞 4자리는 색판별 영역 / 뒤 3자리는 RGB ###
    color_harmonics_vol = [540, 140, 10, 10, 67, 136, 255]
    color_harmonics_curr = [660, 140, 10, 10, 67, 136, 255]

    ### AccuraSM 검사 부분
    mask_m_s_meas_wiring = [5, 33, 248, 54]
    mask_m_s_meas_min_meas_secondary_vol = [268, 33, 506, 54]
    mask_m_s_meas_vt_primary = [5, 58, 248, 79]
    mask_m_s_meas_vt_secondary = [268, 58, 506, 79]
    mask_m_s_meas_primary_reference_voltage_mode = [5, 83, 248, 104]
    mask_m_s_meas_primary_reference_voltage = [268, 83, 506, 104]
    mask_m_s_meas_sliding_reference_voltage = [5, 108, 248, 129]
    mask_m_s_meas_rotating_sequence = [268, 108, 506, 129]
    mask_m_s_meas_ct_primary = [5, 182, 248, 203]
    mask_m_s_meas_ct_secondary = [268, 182, 506, 203]
    mask_m_s_meas_reference_curr = [5, 207, 248, 228]
    mask_m_s_meas_min_meas_curr = [268, 207, 506, 228]
    mask_m_s_meas_tdd_reference_selection = [5, 232, 248, 253]
    mask_m_s_meas_tdd_nominal_curr = [268, 232, 506, 253]
    mask_m_s_meas_subinterval_time = [5, 306, 248, 327]
    mask_m_s_meas_number_of_subintervals = [268, 306, 506, 327]
    mask_m_s_meas_demand_power_type = [5, 331, 248, 352]
    mask_m_s_meas_demand_sync_mode = [268, 331, 506, 352]
    mask_m_s_meas_thermal_response_index = [5, 356, 248, 377]
    mask_m_s_meas_phase_power_calculation = [5, 430, 248, 451]
    mask_m_s_meas_total_power_calculation = [268, 430, 506, 451]
    mask_m_s_meas_pf_sign = [5, 455, 248, 476]
    mask_m_s_meas_pf_value_at_noload = [268, 455, 506, 476]
    mask_m_s_meas_reactive_power_sign = [5, 480, 248, 501]
    mask_m_s_event_dip_trigger = [5, 51, 248, 72]
    mask_m_s_event_dip_threshold = [268, 51, 506, 72]
    mask_m_s_event_dip_hysteresis = [5, 76, 248, 97]
    mask_m_s_event_3dip_trigger = [5, 121, 248, 142]
    mask_m_s_event_3dip_interr_ratio = []
    mask_m_s_event_3dip_interr_delay = []
    mask_m_s_event_swell_trigger = [5, 220, 248, 241]
    mask_m_s_event_swell_threshold = [268, 220, 506, 241]
    mask_m_s_event_swell_hysteresis = [5, 245, 248, 266]
    mask_m_s_event_pq_curve_semi = [5, 319, 248, 340]
    mask_m_s_event_pq_curve_iec = [268, 319, 506, 340]
    mask_m_s_event_pq_curve_itic = [5, 344, 248, 365]

class Configs():
    
    def __init__(self, n=3):
        self.n = n

    def update_n(self, new_n):
        self.n = new_n

    def roi_params(self):
        n = self.n

        self.view0_zone_1 = (160, 120, 630, 350)

        self.view1_zone_1 = (175, 182, 298, 34)
        self.view1_zone_2 = (175, 217, 298, 34)
        self.view2_zone_1 = (476, 182, 305, 34)
        self.view2_zone_2 = (476, 217, 298, 34)
        self.view3_zone_1 = (175, 254, 305, 34)
        self.view3_zone_2 = (175, 289, 298, 34)
        self.view4_zone_1 = (476, 254, 298, 34)
        self.view4_zone_2 = (476, 289, 298, 34)
        self.view5_zone_1 = (175, 326, 298, 34)
        self.view5_zone_2 = (175, 361, 298, 34)
        self.view6_zone_1 = (476, 326, 298, 34)
        self.view6_zone_2 = (476, 361, 298, 34)
        self.view7_zone_1 = (175, 398, 298, 34)
        self.view7_zone_2 = (175, 433, 298, 34)
        self.view8_zone_1 = (476, 398, 298, 34)
        self.view8_zone_2 = (476, 433, 298, 34)
        self.view9_zone_1 = (175, 182, 298, 34)
        self.view9_zone_2 = (175, 217, 298, 34)
        self.view10_zone_1 = (476, 182, 298, 34)
        self.view10_zone_2 = (476, 217, 298, 34)

        self.ref_vol_zone_1 = (175, 361, 234, 34)
        self.ref_vol_zone_2 = (420, 361, 64, 34)
        self.summertime_view1_zone_1 = (175, 182, 269, 34)
        self.summertime_view1_zone_2 = (175, 217, 269, 34)
        self.summertime_view2_zone_1 = (447, 182, 269, 34)
        self.summertime_view2_zone_2 = (447, 217, 269, 34)
        self.summertime_view3_zone_1 = (175, 254, 269, 34)
        self.summertime_view3_zone_2 = (175, 289, 269, 34)
        self.summertime_view4_zone_1 = (447, 254, 269, 34)
        self.summertime_view4_zone_2 = (447, 289, 269, 34)
        self.summertime_view5_zone_1 = (175, 326, 269, 34)
        self.summertime_view5_zone_2 = (175, 361, 269, 34)
        self.summertime_view6_zone_1 = (447, 326, 269, 34)
        self.summertime_view6_zone_2 = (447, 361, 269, 34)
        self.summertime_view7_zone_1 = (175, 398, 269, 34)
        self.summertime_view7_zone_2 = (175, 433, 269, 34)
        self.summertime_view8_zone_1 = (447, 398, 269, 34)
        self.summertime_view8_zone_2 = (447, 433, 269, 34)

        def scale_coord(coords):
            """좌표 [x, y, w, h]에 n을 곱합니다."""
            if coords is None: return None 
            return [int(n * x) for x in coords]
        
        params = {

            # OCR 결과를 위한 좌표
            # rms voltage l-l l-m min max
            ConfigROI.title_view: [n*x for x in [160, 120, 620, 53]],
            ConfigROI.a_ab: [n*x for x in [175, 179, 135, 70]],  # AB
            ConfigROI.a_time_stamp: [n*x for x in [320, 220, 190, 25]], # time stamp
            ConfigROI.a_meas: [n*x for x in [540, 190, 230, 55]],  # 190.0 V
            ConfigROI.b_bc: [n*x for x in [165, 253, 135, 69]],  # BC
            ConfigROI.b_time_stamp: [n*x for x in [320, 293, 190, 25]], # time stamp
            ConfigROI.b_meas: [n*x for x in [540, 260, 230, 60]],  # 190.0 V
            ConfigROI.c_ca: [n*x for x in [165, 326, 135, 69]],  # CA
            ConfigROI.c_time_stamp: [n*x for x in [320, 365, 190, 25]], # time stamp
            ConfigROI.c_meas: [n*x for x in [540, 340, 230, 50]],  # 190.0 V
            ConfigROI.aver: [n*x for x in [165, 399, 135, 69]],  # Average
            ConfigROI.aver_time_stamp: [n*x for x in [320, 438, 190, 25]], # time stamp
            ConfigROI.aver_meas: [n*x for x in [540, 410, 230, 60]],  # 190.0

            ### 확인 후 제거 ###
            "main_view_5": [n*x for x in [720, 200, 35, 40]],  # V
            "main_view_9": [n*x for x in [720, 270, 35, 40]],  # V
            "main_view_13": [n*x for x in [720, 350, 35, 40]],  # V
            "main_view_17": [n*x for x in [720, 420, 35, 40]],  # V

            # current % meas 수치 해야됨
            ConfigROI.curr_per_a: [n*x for x in [360, 190, 120, 30]],
            ConfigROI.curr_per_b: [n*x for x in [360, 265, 120, 30]],
            ConfigROI.curr_per_c: [n*x for x in [360, 335, 120, 30]],
            ConfigROI.curr_per_aver: [n*x for x in [360, 405, 120, 35]],

            # test mode confirm
            "999": [n*x for x in [220, 105, 350, 40]],

            # Phasor
            ConfigROI.phasor_img_cut: [176, 179, 425, 295],
            ConfigROI.phasor_title: [n*x for x in [160, 130, 140, 40]], # Phasor
            ConfigROI.phasor_title_2: [n*x for x in [530, 130, 246, 40]], # [V]Voltage, [V]Current
            ConfigROI.phasor_view_2: [n*x for x in [480, 120, 310, 53]], # [V]Voltage, [V]Current
            ConfigROI.phasor_vl_vn: [n*x for x in [570, 190, 210, 39]],  # VLL VLN
            ConfigROI.phasor_voltage: [n*x for x in [465, 235, 80, 27]],  # Voltage
            ConfigROI.phasor_a_c_vol: [n*x for x in [550, 234, 55, 76]], # AB,BC,CA or A,B,C
            ConfigROI.phasor_a_meas: [n*x for x in [610, 236, 95, 23]],  # A-전압수치
            ConfigROI.phasor_a_angle: [n*x for x in [705, 236, 58, 23]],  # A-각도수치
            ConfigROI.phasor_b_meas: [n*x for x in [610, 260, 95, 23]],  # B-전압수치
            ConfigROI.phasor_b_angle: [n*x for x in [705, 260, 58, 23]],  # B-각도수치
            ConfigROI.phasor_c_meas: [n*x for x in [610, 284, 95, 23]],  # C-전압수치
            ConfigROI.phasor_c_angle: [n*x for x in [705, 284, 58, 23]],  # C-각도수치
            ConfigROI.phasor_a_c_angle_vol: [763, 236, 14, 66],  # A~C-각도기호
            ConfigROI.phasor_current: [n*x for x in [465, 345, 80, 24]],  # Current
            ConfigROI.phasor_a_c_cur: [n*x for x in [550, 345, 55, 76]],  # A,B,C
            ConfigROI.phasor_a_meas_cur: [n*x for x in [610, 346, 95, 23]],  # A-전류수치
            ConfigROI.phasor_a_angle_cur: [n*x for x in [705, 346, 58, 23]],  # A-각도수치
            ConfigROI.phasor_b_meas_cur: [n*x for x in [610, 370, 95, 23]],  # B-전류수치
            ConfigROI.phasor_b_angle_cur: [n*x for x in [705, 370, 58, 23]],  # B-각도수치
            ConfigROI.phasor_c_meas_cur: [n*x for x in [610, 394, 95, 23]],  # C-전류수치
            ConfigROI.phasor_c_angle_cur: [n*x for x in [705, 394, 58, 23]],  # C-각도수치
            ConfigROI.phasor_a_c_angle_cur: [763, 394, 14, 21], # A~C-각도기호

            # harmonics
            ConfigROI.harmonics_img_cut: [170, 260, 600, 213],
            ConfigROI.harmonics_text_img: [n*x for x in [165, 230, 620, 240]],
            ConfigROI.harmonics_title: [n*x for x in [160, 120, 630, 53]],
            ConfigROI.harmonics_sub_title_1: [n*x for x in [160, 180, 270, 80]], # dropdown 버튼 + THD Fund.
            ConfigROI.harmonics_sub_title_2: [n*x for x in [440, 180, 130, 40]], # Fund.
            ConfigROI.harmonics_sub_title_3: [n*x for x in [580, 180, 2000, 40]], # Fund.
            ConfigROI.harmonics_text_title: [n*x for x in [160, 180, 620, 40]],
            ConfigROI.harmonics_text_sub_title : [n*x for x in [160, 180, 270, 40]],
            ConfigROI.harmonics_text_sub_abc : [n*x for x in [590, 180, 190, 40]],
            ConfigROI.harmonics_graph_a : [n*x for x in [435, 220, 15, 21]],
            ConfigROI.harmonics_graph_b : [n*x for x in [555, 220, 15, 21]],
            ConfigROI.harmonics_graph_c : [n*x for x in [675, 220, 15, 21]],
            ConfigROI.harmonics_thd_a : [n*x for x in [465, 220, 70, 21]],
            ConfigROI.harmonics_thd_b : [n*x for x in [585, 220, 70, 21]],
            ConfigROI.harmonics_thd_c : [n*x for x in [705, 220, 70, 21]],
            ConfigROI.harmonics_fund_a : [n*x for x in [465, 241, 70, 23]],
            ConfigROI.harmonics_fund_b : [n*x for x in [585, 241, 70, 23]],
            ConfigROI.harmonics_fund_c : [n*x for x in [705, 241, 70, 23]],

            #Waveform
            ConfigROI.waveform_all_img_cut: [170, 179, 610, 286],
            ConfigROI.waveform_graph_img_cut: [313, 253, 411, 203],
            ConfigROI.waveform_title: [n*x for x in [160, 120, 630, 53]],
            ConfigROI.harmonics_graph_img_cut: [313, 283, 455, 173],
            ConfigROI.harmonics_chart_img_cut: [250, 260, 495, 214],
            ConfigROI.harmonics_text_number_title_1: [n*x for x in [175, 237, 30, 225]],
            ConfigROI.harmonics_text_number_meas_1: [n*x for x in [206, 238, 67, 232]],
            ConfigROI.harmonics_text_chart_img_cut_3: [n*x for x in [170, 389, 610, 240]],

            #meter>setup>measurement>voltage
            ConfigROI.s_wiring_1: scale_coord(self.view1_zone_1),
            ConfigROI.s_wiring_2: scale_coord(self.view1_zone_2),
            ConfigROI.s_min_meas_sec_ln_vol_1: scale_coord(self.view2_zone_1),
            ConfigROI.s_min_meas_sec_ln_vol_2: scale_coord(self.view2_zone_2),
            ConfigROI.s_vt_primary_ll_vol_1: scale_coord(self.view3_zone_1),
            ConfigROI.s_vt_primary_ll_vol_2: scale_coord(self.view3_zone_2),
            ConfigROI.s_vt_secondary_ll_vol_1: scale_coord(self.view4_zone_1),
            ConfigROI.s_vt_secondary_ll_vol_2: scale_coord(self.view4_zone_2),
            ConfigROI.s_primary_reference_vol_1: scale_coord(self.view5_zone_1),
            ConfigROI.s_primary_reference_vol_2: scale_coord(self.view5_zone_2),
            ConfigROI.s_primary_reference_vol_3: scale_coord(self.view5_zone_2),
            ConfigROI.s_primary_reference_vol_4: scale_coord(self.view5_zone_2),
            ConfigROI.s_sliding_reference_vol_1: scale_coord(self.view6_zone_1),
            ConfigROI.s_sliding_reference_vol_2: scale_coord(self.view6_zone_2),
            ConfigROI.s_rotation_sequence_1: scale_coord(self.view7_zone_1),
            ConfigROI.s_rotation_sequence_2: scale_coord(self.view7_zone_2),
            #current
            ConfigROI.s_ct_primary_curr_1: scale_coord(self.view1_zone_1),
            ConfigROI.s_ct_primary_curr_2: scale_coord(self.view1_zone_2),
            ConfigROI.s_ct_secondary_curr_1: scale_coord(self.view2_zone_1),
            ConfigROI.s_ct_secondary_curr_2: scale_coord(self.view2_zone_2),
            ConfigROI.s_reference_curr_1: scale_coord(self.view3_zone_1),
            ConfigROI.s_reference_curr_2: scale_coord(self.view3_zone_2),
            ConfigROI.s_min_meas_curr_1: scale_coord(self.view4_zone_1),
            ConfigROI.s_min_meas_curr_2: scale_coord(self.view4_zone_2),
            ConfigROI.s_tdd_reference_selection_1: scale_coord(self.view5_zone_1),
            ConfigROI.s_tdd_reference_selection_2: scale_coord(self.view5_zone_2),
            ConfigROI.s_tdd_nominal_curr_1: scale_coord(self.view6_zone_1),
            ConfigROI.s_tdd_nominal_curr_2: scale_coord(self.view6_zone_2),
            #demand
            ConfigROI.s_sub_interval_time_1: scale_coord(self.view1_zone_1),
            ConfigROI.s_sub_interval_time_2: scale_coord(self.view1_zone_2),
            ConfigROI.s_number_of_sub_intervals_1: scale_coord(self.view2_zone_1),
            ConfigROI.s_number_of_sub_intervals_2: scale_coord(self.view2_zone_2),
            ConfigROI.s_demand_power_type_1: scale_coord(self.view3_zone_1),
            ConfigROI.s_demand_power_type_2: scale_coord(self.view3_zone_2),
            ConfigROI.s_demand_sync_mode_1: scale_coord(self.view4_zone_1),
            ConfigROI.s_demand_sync_mode_2: scale_coord(self.view4_zone_2),
            ConfigROI.s_thermal_response_index_1: scale_coord(self.view5_zone_1),
            ConfigROI.s_thermal_response_index_2: scale_coord(self.view5_zone_2),
            #power
            ConfigROI.s_phase_power_calculation_1: scale_coord(self.view1_zone_1),
            ConfigROI.s_phase_power_calculation_2: scale_coord(self.view1_zone_2),
            ConfigROI.s_total_power_calculation_1: scale_coord(self.view2_zone_1),
            ConfigROI.s_total_power_calculation_2: scale_coord(self.view2_zone_2),
            ConfigROI.s_pf_sign_1: scale_coord(self.view3_zone_1),
            ConfigROI.s_pf_sign_2: scale_coord(self.view3_zone_2),
            ConfigROI.s_pf_value_at_noload_1: scale_coord(self.view4_zone_1),
            ConfigROI.s_pf_value_at_noload_2: scale_coord(self.view4_zone_2),
            ConfigROI.s_reactive_power_sign_1: scale_coord(self.view5_zone_1),
            ConfigROI.s_reactive_power_sign_2: scale_coord(self.view5_zone_2),

            # event>dip
            ConfigROI.s_dip_trigger_1: scale_coord(self.view1_zone_1),
            ConfigROI.s_dip_trigger_2: scale_coord(self.view1_zone_2),
            ConfigROI.s_dip_threshold_1: scale_coord(self.view2_zone_1),
            ConfigROI.s_dip_threshold_2: scale_coord(self.view2_zone_2),
            ConfigROI.s_dip_hysteresis_1: scale_coord(self.view3_zone_1),
            ConfigROI.s_dip_hysteresis_2: scale_coord(self.view3_zone_2),
            ConfigROI.s_dip_3phase_dip_1: [n*x for x in [175, 331, 298, 34]],
            ConfigROI.s_dip_3phase_dip_2: [n*x for x in [175, 366, 298, 34]],
            #swell
            ConfigROI.s_swell_trigger_1: scale_coord(self.view1_zone_1),
            ConfigROI.s_swell_trigger_2: scale_coord(self.view1_zone_2),
            ConfigROI.s_swell_threshold_1: scale_coord(self.view2_zone_1),
            ConfigROI.s_swell_threshold_2: scale_coord(self.view2_zone_2),
            ConfigROI.s_swell_hysteresis_1: scale_coord(self.view3_zone_1),
            ConfigROI.s_swell_hysteresis_2: scale_coord(self.view3_zone_2),
            #pq curve
            ConfigROI.s_pq_curve_semi_1: scale_coord(self.view1_zone_1),
            ConfigROI.s_pq_curve_semi_2: scale_coord(self.view1_zone_2),
            ConfigROI.s_pq_curve_iec_1: scale_coord(self.view2_zone_1),
            ConfigROI.s_pq_curve_iec_2: scale_coord(self.view2_zone_2),
            ConfigROI.s_pq_curve_itic_1: scale_coord(self.view3_zone_1),
            ConfigROI.s_pq_curve_itic_2: scale_coord(self.view3_zone_2),

            #network>ethernet
            #rs-485
            ConfigROI.s_device_address_1: scale_coord(self.view1_zone_1),
            ConfigROI.s_device_address_2: scale_coord(self.view1_zone_2),
            ConfigROI.s_bit_rate_1: scale_coord(self.view2_zone_1),
            ConfigROI.s_bit_rate_2: scale_coord(self.view2_zone_2),
            ConfigROI.s_parity_1: scale_coord(self.view3_zone_1),
            ConfigROI.s_parity_2: scale_coord(self.view3_zone_2),
            ConfigROI.s_stop_bit_1: scale_coord(self.view4_zone_1),
            ConfigROI.s_stop_bit_2: scale_coord(self.view4_zone_2),
            #advanced
            ConfigROI.s_modbus_timeout_1: scale_coord(self.view1_zone_1),
            ConfigROI.s_modbus_timeout_2: scale_coord(self.view1_zone_2),
            ConfigROI.s_rstp_1: scale_coord(self.view2_zone_1),
            ConfigROI.s_rstp_2: scale_coord(self.view2_zone_2),
            ConfigROI.s_storm_control_1: scale_coord(self.view3_zone_1),
            ConfigROI.s_storm_control_2: scale_coord(self.view3_zone_2),
            ConfigROI.s_rs485_map_1: scale_coord(self.view4_zone_1),
            ConfigROI.s_rs485_map_2: scale_coord(self.view4_zone_2),
            ConfigROI.s_remote_control_lock_mode_1: scale_coord(self.view5_zone_1),
            ConfigROI.s_remote_control_lock_mode_2: scale_coord(self.view5_zone_2),

            #control>data reset
            ConfigROI.s_data_reset_demand: scale_coord(self.view1_zone_1),
            ConfigROI.s_data_reset_peak_demand: scale_coord(self.view2_zone_1),
            ConfigROI.s_data_reset_max_min: scale_coord(self.view3_zone_1),
            ConfigROI.s_data_reset_energy: scale_coord(self.view4_zone_1),
            ConfigROI.s_data_reset_pq_event: scale_coord(self.view5_zone_1),
            #demand sync
            ConfigROI.s_demand_sync: scale_coord(self.view1_zone_1),
            #test mode
            ConfigROI.s_test_mode_1: scale_coord(self.view1_zone_1),
            ConfigROI.s_test_mode_2: scale_coord(self.view1_zone_2),
            ConfigROI.s_test_mode_timeout_1: scale_coord(self.view2_zone_1),
            ConfigROI.s_test_mode_timeout_2: scale_coord(self.view2_zone_2),

            #system>description
            ConfigROI.s_installation_year_1: scale_coord(self.view4_zone_1),
            ConfigROI.s_installation_year_2: scale_coord(self.view4_zone_2),
            ConfigROI.s_installation_month_1: scale_coord(self.view5_zone_1),
            ConfigROI.s_installation_month_2: scale_coord(self.view5_zone_2),
            ConfigROI.s_installation_day_1: scale_coord(self.view6_zone_1),
            ConfigROI.s_installation_day_2: scale_coord(self.view6_zone_2),
            #locale
            ConfigROI.s_timezone_offset_1: scale_coord(self.view1_zone_1),
            ConfigROI.s_timezone_offset_2: scale_coord(self.view1_zone_2),
            ConfigROI.s_temperature_unit_1: scale_coord(self.view2_zone_1),
            ConfigROI.s_temperature_unit_2: scale_coord(self.view2_zone_2),
            ConfigROI.s_energy_unit_1: scale_coord(self.view3_zone_1),
            ConfigROI.s_energy_unit_2: scale_coord(self.view3_zone_2),
            ConfigROI.s_date_format_1: scale_coord(self.view4_zone_1),
            ConfigROI.s_date_format_2: scale_coord(self.view4_zone_2),
            #local time
            ConfigROI.s_year_1: scale_coord(self.view1_zone_1),
            ConfigROI.s_year_2: scale_coord(self.view1_zone_2),
            ConfigROI.s_month_1: scale_coord(self.view2_zone_1),
            ConfigROI.s_month_2: scale_coord(self.view2_zone_2),
            ConfigROI.s_day_1: scale_coord(self.view3_zone_1),
            ConfigROI.s_day_2: scale_coord(self.view3_zone_2),
            ConfigROI.s_hour_1: scale_coord(self.view4_zone_1),
            ConfigROI.s_hour_2: scale_coord(self.view4_zone_2),
            ConfigROI.s_minute_1: scale_coord(self.view5_zone_1),
            ConfigROI.s_minute_2: scale_coord(self.view5_zone_2),
            ConfigROI.s_second_1: scale_coord(self.view6_zone_1),
            ConfigROI.s_second_2: scale_coord(self.view6_zone_2),
            #summer time
            ConfigROI.s_summer_time_mode_1: scale_coord(self.summertime_view1_zone_1),
            ConfigROI.s_summer_time_mode_2: scale_coord(self.summertime_view1_zone_2),
            ConfigROI.s_summer_time_time_offset_1: scale_coord(self.summertime_view2_zone_1),
            ConfigROI.s_summer_time_time_offset_2: scale_coord(self.summertime_view2_zone_2),
            ConfigROI.s_start_month_1: scale_coord(self.summertime_view3_zone_1),
            ConfigROI.s_start_month_2: scale_coord(self.summertime_view3_zone_2),
            ConfigROI.s_start_nth_weekday_1: scale_coord(self.summertime_view4_zone_1),
            ConfigROI.s_start_nth_weekday_2: scale_coord(self.summertime_view4_zone_2),
            ConfigROI.s_start_weekday_1: scale_coord(self.summertime_view5_zone_1),
            ConfigROI.s_start_weekday_2: scale_coord(self.summertime_view5_zone_2),
            ConfigROI.s_start_minute_1: scale_coord(self.summertime_view6_zone_1),
            ConfigROI.s_start_minute_2: scale_coord(self.summertime_view6_zone_2),
            ConfigROI.s_end_month_1: scale_coord(self.summertime_view7_zone_1),
            ConfigROI.s_end_month_2: scale_coord(self.summertime_view7_zone_2),
            ConfigROI.s_end_nth_weekday_1: scale_coord(self.summertime_view8_zone_1),
            ConfigROI.s_end_nth_weekday_2: scale_coord(self.summertime_view8_zone_2),
            ConfigROI.s_end_weekday_1: scale_coord(self.summertime_view1_zone_1),
            ConfigROI.s_end_weekday_2: scale_coord(self.summertime_view1_zone_2),
            ConfigROI.s_end_minute_1: scale_coord(self.summertime_view2_zone_1),
            ConfigROI.s_end_minute_2: scale_coord(self.summertime_view2_zone_2),
            #ntp
            ConfigROI.s_sync_mode_1: scale_coord(self.view2_zone_1),
            ConfigROI.s_sync_mode_2: scale_coord(self.view2_zone_2),
            ConfigROI.s_sync_period_1: scale_coord(self.view3_zone_1),
            ConfigROI.s_sync_period_2: scale_coord(self.view3_zone_2),
            ConfigROI.s_sync_max_drift_1: scale_coord(self.view4_zone_1),
            ConfigROI.s_sync_max_drift_2: scale_coord(self.view4_zone_2),
            #lcd&buzzer
            ConfigROI.s_lcd_backlight_timeout_1: scale_coord(self.view1_zone_1),
            ConfigROI.s_lcd_backlight_timeout_2: scale_coord(self.view1_zone_2),
            ConfigROI.s_lcd_backlight_low_level_1: scale_coord(self.view2_zone_1),
            ConfigROI.s_lcd_backlight_low_level_2: scale_coord(self.view2_zone_2),
            ConfigROI.s_buzzer_for_button_1: scale_coord(self.view3_zone_1),
            ConfigROI.s_buzzer_for_button_2: scale_coord(self.view3_zone_2),

        }

        return params