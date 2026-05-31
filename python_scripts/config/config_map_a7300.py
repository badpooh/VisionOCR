# -*- coding: utf-8 -*-
# A7300 제품 전용 Modbus 주소 맵.
# - 이 파일은 기존 config_map.py(= A7300 원본)와 동일한 내용.
# - A3700N / A2700 은 각각 config_map_a3700n.py / config_map_a2700.py 를 참조한다.
# - 새 제품을 추가하면 config_product.get_map_module() 로더에도 등록할 것.

from enum import Enum

class ConfigMap(Enum):
    ### modbus map 에서 -1 값 ###
    addr_reset_max_min = (12002, 1)

    ### measurement setup ###
    ### UINT16 ###
    addr_measurement_setup_access = {'address': 6000, 'count': 1}
    addr_wiring = (6001, 1)
    addr_vt_secondary_ll_voltage = (6007, 1)
    addr_min_measured_secondary_ln_voltage = (6008, 1)
    addr_reference_voltage_mode = (6009, 1)
    addr_ct_secondary_current = (6019, 1)
    addr_min_measured_current = (6020, 1)
    addr_tdd_reference = (6023, 1)
    addr_demand_sync_mode = (6028, 1)
    addr_num_of_sub_interval = (6029, 1)
    addr_sub_interval_time = (6030, 1)
    addr_thermal_response_index = (6031, 1)
    addr_demand_power_type = (6032, 1)
    addr_phase_power_calculation = (6033, 1)
    addr_total_power_calculation = (6034, 1)
    addr_pf_value_at_no_load = (6035, 1)
    addr_pf_sign = (6036, 1)
    addr_reactive_power_sign = (6037, 1)
    # addr_default_frequency = (6038, 1)
    # addr_max_harmonic_order = (6039, 1)
    addr_rotating_sequence = (6040, 1)
    addr_sliding_reference_voltage_setup_access = {'address': 6050, 'count': 1}
    addr_sliding_reference_voltage_type = (6051, 1)
    addr_aggregation_selection = {'address': 14900, 'count': 1}
    ### UINT32 ###
    addr_reference_voltage = (6003, 2)
    addr_vt_primary_ll_voltage = (6005, 2)
    addr_reference_current = (6015, 2)
    addr_ct_primary_current = (6017, 2)
    addr_nominal_tdd_current = (6021, 2)

    ### Measurement Data ###
    ### FLOAT ###
    addr_meas_van = (15000, 2)
    addr_meas_vbn = (15002, 2)
    addr_meas_vcn = (15004, 2)
    addr_meas_vavg_ln = (15006, 2)
    addr_meas_vrsd = (15008, 2)
    addr_meas_vab = (15010, 2)
    addr_meas_vbc = (15012, 2)
    addr_meas_vca = (15014, 2)
    addr_meas_vavg_ll = (15016, 2)
    addr_meas_ia = (15018, 2)
    addr_meas_ib = (15020, 2)
    addr_meas_ic = (15022, 2)
    addr_meas_iavg = (15024, 2)
    addr_meas_irsd = (15026, 2)
    addr_meas_fund_van = (15028, 2)
    addr_meas_fund_vbn = (15030, 2)
    addr_meas_fund_vcn = (15032, 2)
    addr_meas_fund_vavg_ln = (15034, 2)
    addr_meas_fund_vrsd = (15036, 2)
    addr_meas_fund_vab = (15038, 2)
    addr_meas_fund_vbc = (15040, 2)
    addr_meas_fund_vca = (15042, 2)
    addr_meas_fund_vavg_ll = (15044, 2)
    addr_meas_fund_ia = (15046, 2)
    addr_meas_fund_ib = (15048, 2)
    addr_meas_fund_ic = (15050, 2)
    addr_meas_fund_iavg = (15052, 2)
    addr_meas_fund_irsd = (15054, 2)
    addr_meas_frequency = (15056, 2)
    addr_meas_thd_van = (15058, 2)
    addr_meas_thd_vbn = (15060, 2)
    addr_meas_thd_vcn = (15062, 2)
    addr_meas_thd_vab = (15064, 2)
    addr_meas_thd_vbc = (15066, 2)
    addr_meas_thd_vca = (15068, 2)
    addr_meas_thd_ia = (15070, 2)
    addr_meas_thd_ib = (15072, 2)
    addr_meas_thd_ic = (15074, 2)
    addr_meas_tdd_ia = (15076, 2)
    addr_meas_tdd_ib = (15078, 2)
    addr_meas_tdd_ic = (15080, 2)
    addr_meas_cf_ia = (15082, 2)
    addr_meas_cf_ib = (15084, 2)
    addr_meas_cf_ic = (15086, 2)
    addr_meas_kf_ia = (15088, 2)
    addr_meas_kf_ib = (15090, 2)
    addr_meas_kf_ic = (15092, 2)
    addr_meas_pa = (15094, 2)
    addr_meas_pb = (15096, 2)
    addr_meas_pc = (15098, 2)
    addr_meas_p_total = (15100, 2)
    addr_meas_qa = (15102, 2)
    addr_meas_qb = (15104, 2)
    addr_meas_qc = (15106, 2)
    addr_meas_q_total = (15108, 2)
    addr_meas_sa = (15110, 2)
    addr_meas_sb = (15112, 2)
    addr_meas_sc = (15114, 2)
    addr_meas_s_total = (15116, 2)
    addr_meas_pfa = (15118, 2)
    addr_meas_pfb = (15120, 2)
    addr_meas_pfc = (15122, 2)
    addr_meas_pf_total = (15124, 2)
    addr_meas_demand_ia = (15170, 2)
    addr_meas_demand_ib = (15172, 2)
    addr_meas_demand_ic = (15174, 2)
    addr_meas_demand_iavg = (15176, 2)
    addr_meas_demand_pa = (15178, 2)
    addr_meas_demand_pb = (15180, 2)
    addr_meas_demand_pc = (15182, 2)
    addr_meas_demand_ptotal = (15184, 2)
    addr_meas_vol_positive_sequence_ln = (15146, 2)
    addr_meas_vol_negative_sequence_ln = (15148, 2)
    addr_meas_vol_zero_sequence_ln = (15150, 2)
    addr_meas_vol_positive_sequence_ll = (15152, 2)
    addr_meas_vol_negative_sequence_ll = (15154, 2)
    addr_meas_vol_unbalance_ln = (15138, 2)
    addr_meas_vol_unbalance_ll = (15140, 2)
    addr_meas_vol_zero_unbalance = (15142, 2)
    addr_meas_vol_negative_unbalance = (15144, 2)
    addr_meas_curr_unbalance = (15156, 2)
    addr_meas_curr_zero_unbalance = (15158, 2)
    addr_meas_curr_negative_unbalance = (15160, 2)
    addr_meas_curr_positive_sequence = (15162, 2)
    addr_meas_curr_negative_sequence = (15164, 2)
    addr_meas_curr_zero_sequence = (15166, 2)

    addr_meas_min_van = (31200, 2)
    addr_meas_min_vbn = (31202, 2)
    addr_meas_min_vcn = (31204, 2)
    addr_meas_min_vavg_ln = (31206, 2)
    addr_meas_min_vrsd = (31208, 2)
    addr_meas_min_vab = (31210, 2)
    addr_meas_min_vbc = (31212, 2)
    addr_meas_min_vca = (31214, 2)
    addr_meas_min_vavg_ll = (31216, 2)
    addr_meas_fund_min_van = (31228, 2)
    addr_meas_fund_min_vbn = (31230, 2)
    addr_meas_fund_min_vcn = (31232, 2)
    addr_meas_fund_min_vavg_ln = (31234, 2)
    addr_meas_fund_min_vrsd = (31236, 2)
    addr_meas_fund_min_vab = (31238, 2)
    addr_meas_fund_min_vbc = (31240, 2)
    addr_meas_fund_min_vca = (31242, 2)
    addr_meas_fund_min_vavg_ll = (31244, 2)
    addr_meas_freq_min = (31296, 2)

    addr_meas_min_ia = (31218, 2)
    addr_meas_min_ib = (31220, 2)
    addr_meas_min_ic = (31222, 2)
    addr_meas_min_iavg = (31224, 2)
    addr_meas_min_irsd = (31226, 2)
    addr_meas_fund_min_ia = (31246, 2)
    addr_meas_fund_min_ib = (31248, 2)
    addr_meas_fund_min_ic = (31250, 2)
    addr_meas_fund_min_iavg = (31252, 2)
    addr_meas_fund_min_irsd = (31254, 2)

    addr_meas_min_pa = (31256, 2)
    addr_meas_min_pb = (31258, 2)
    addr_meas_min_pc = (31260, 2)
    addr_meas_min_ptotal = (31262, 2)
    addr_meas_min_qa = (31264, 2)
    addr_meas_min_qb = (31266, 2)
    addr_meas_min_qc = (31268, 2)
    addr_meas_min_qtotal = (31270, 2)
    addr_meas_min_sa = (31272, 2)
    addr_meas_min_sb = (31274, 2)
    addr_meas_min_sc = (31276, 2)
    addr_meas_min_stotal = (31278, 2)
    addr_meas_min_pfa = (31280, 2)
    addr_meas_min_pfb = (31282, 2)
    addr_meas_min_pfc = (31284, 2)
    addr_meas_min_pftotal = (31286, 2)

    addr_meas_max_van = (31000, 2)
    addr_meas_max_vbn = (31002, 2)
    addr_meas_max_vcn = (31004, 2)
    addr_meas_max_vavg_ln = (31006, 2)
    addr_meas_max_vrsd = (31008, 2)
    addr_meas_max_vab = (31010, 2)
    addr_meas_max_vbc = (31012, 2)
    addr_meas_max_vca = (31014, 2)
    addr_meas_max_vavg_ll = (31016, 2)
    addr_meas_fund_max_van = (31028, 2)
    addr_meas_fund_max_vbn = (31030, 2)
    addr_meas_fund_max_vcn = (31032, 2)
    addr_meas_fund_max_vavg_ln = (31034, 2)
    addr_meas_fund_max_vrsd = (31036, 2)
    addr_meas_fund_max_vab = (31038, 2)
    addr_meas_fund_max_vbc = (31040, 2)
    addr_meas_fund_max_vca = (31042, 2)
    addr_meas_fund_max_vavg_ll = (31044, 2)
    addr_meas_thd_max_van = (31098, 2)
    addr_meas_thd_max_vbn = (31100, 2)
    addr_meas_thd_max_vcn = (31102, 2)
    addr_meas_thd_max_vab = (31104, 2)
    addr_meas_thd_max_vbc = (31106, 2)
    addr_meas_thd_max_vca = (31108, 2)
    addr_meas_freq_max = (31096, 2)

    addr_meas_max_ia = (31018, 2)
    addr_meas_max_ib = (31020, 2)
    addr_meas_max_ic = (31022, 2)
    addr_meas_max_iavg = (31024, 2)
    addr_meas_max_irsd = (31026, 2)
    addr_meas_fund_max_ia = (31046, 2)
    addr_meas_fund_max_ib = (31048, 2)
    addr_meas_fund_max_ic = (31050, 2)
    addr_meas_fund_max_iavg = (31052, 2)
    addr_meas_fund_max_irsd = (31054, 2)
    addr_meas_thd_max_ia = (31110, 2)
    addr_meas_thd_max_ib = (31112, 2)
    addr_meas_thd_max_ic = (31114, 2)
    addr_meas_tdd_max_ia = (31116, 2)
    addr_meas_tdd_max_ib = (31118, 2)
    addr_meas_tdd_max_ic = (31120, 2)
    addr_meas_cf_max_ia = (31122, 2)
    addr_meas_cf_max_ib = (31124, 2)
    addr_meas_cf_max_ic = (31126, 2)
    addr_meas_kf_max_ia = (31128, 2)
    addr_meas_kf_max_ib = (31130, 2)
    addr_meas_kf_max_ic = (31132, 2)
    addr_meas_demand_max_ia = (31166, 2)
    addr_meas_demand_max_ib = (31168, 2)
    addr_meas_demand_max_ic = (31170, 2)
    addr_meas_demand_max_iavg = (31172, 2)
    addr_meas_max_pa = (31056, 2)
    addr_meas_max_pb = (31058, 2)
    addr_meas_max_pc = (31060, 2)
    addr_meas_max_ptotal = (31062, 2)
    addr_meas_max_qa = (31064, 2)
    addr_meas_max_qb = (31066, 2)
    addr_meas_max_qc = (31068, 2)
    addr_meas_max_qtotal = (31070, 2)
    addr_meas_max_sa = (31072, 2)
    addr_meas_max_sb = (31074, 2)
    addr_meas_max_sc = (31076, 2)
    addr_meas_max_stotal = (31078, 2)
    addr_meas_max_pfa = (31080, 2)
    addr_meas_max_pfb = (31082, 2)
    addr_meas_max_pfc = (31084, 2)
    addr_meas_max_pftotal = (31086, 2)
    addr_meas_demand_max_pa = (31174, 2)
    addr_meas_demand_max_pb = (31176, 2)
    addr_meas_demand_max_pc = (31178, 2)
    addr_meas_demand_max_ptotal = (31180, 2)
    addr_meas_vol_positive_sequence_max_ln = (31148, 2)
    addr_meas_vol_negative_sequence_max_ln = (31150, 2)
    addr_meas_vol_zero_sequence_max_ln = (31152, 2)
    addr_meas_vol_positive_sequence_max_ll = (31154, 2)
    addr_meas_vol_negative_sequence_max_ll = (31156, 2)
    addr_meas_vol_unbalance_max_ll = (31136, 2)
    addr_meas_vol_unbalance_max_ln = (31134, 2)
    addr_meas_vol_zero_unbalance_max = (31138, 2)
    addr_meas_vol_negative_unbalance_max = (31140, 2)
    addr_meas_curr_unbalance_max = (31142, 2)
    addr_meas_curr_zero_unbalance_max = (31144, 2)
    addr_meas_curr_negative_unbalance_max = (31146, 2)
    addr_meas_curr_positive_sequence_max = (31158, 2)
    addr_meas_curr_negative_sequence_max = (31160, 2)
    addr_meas_curr_zero_sequence_max = (31162, 2)
    
    ### Measurement Data Min Timestamp ###
    ### FLOAT ###
    addr_timestamp_van = (31500, 2)
    addr_timestamp_vbn = (31502, 2)
    addr_timestamp_vcn = (31504, 2)
    addr_timestamp_vavg_ln = (31506, 2)
    addr_timestamp_vrsd = (31508, 2)
    addr_timestamp_vab = (31510, 2)
    addr_timestamp_vbc = (31512, 2)
    addr_timestamp_vca = (31514, 2)
    addr_timestamp_vavg_ll = (31516, 2)

    ### meter event setup ###
    addr_dip_setup_access = (5100, 1)
    addr_dip = (5101, 1)
    addr_dip_threshold = (5102, 1)
    addr_dip_hysteresis = (5103, 1)
    addr_3phase_dip_setup_access = (5110, 1)
    addr_3phase_dip = (5111, 1)
    addr_swell_setup_access = (5120, 1)
    addr_swell = (5121, 1)
    addr_swell_threshold = (5122, 1)
    addr_swell_hysteresis = (5123, 1)
    addr_semi_event_setup_access = (5160, 1)
    addr_semi = (5161, 1)
    addr_itic_event_setup_access = (5190, 1)
    addr_itic = (5191, 1)
    addr_iec_event_setup_access = (5220, 1)
    addr_iec = (5221, 1)

    ### meter network setup ###
    addr_dhcp_setup_access = (3720, 1)
    addr_dhcp = (3721, 1)
    addr_rs485_setup_access = (3700, 1)
    addr_device_address = (3701, 1)
    addr_bit_rate = (3702, 1)
    addr_parity = (3703, 1)
    addr_stop_bit = (3704, 1)
    addr_modbus_timeout_setup_access = (3620, 1)
    addr_modbus_timeout = (3621, 1)
    addr_rstp_setup_access = (3640, 1)
    addr_rstp = (3641, 1)
    addr_storm_control_setup_access = (3680, 1)
    addr_storm_control = (3681, 1)
    addr_rs485_map_setup_access = (3630, 1)
    addr_rs485_map = (3631, 1)
    addr_remote_control_lock_mode_access = (3400, 1)
    addr_remote_control_lock_mode = (3401, 1)

    ### meter control ###
    addr_meter_test_mode = (4000, 1)
    addr_meter_demo_mode_timeout_setup_access = (4001, 1)
    addr_meter_demo_mode_timeout = (4002, 1)

    ### meter system ###
    addr_description_setup_access = (3300, 1)
    addr_installation_year = (3331, 1)
    addr_installation_month = (3332, 1)
    addr_installation_day = (3333, 1)
    addr_locale_setup_access = (3020, 1)
    addr_timezone_offset = (3021, 1)
    addr_temperature_unit = (3022, 1)
    addr_energy_unit = (3023, 1)
    addr_date_display_format = (3024, 1)
    addr_system_time_setup_access = (3060, 1)
    addr_summer_time_setup_access = (3000, 1)
    addr_summer_time = (3001, 1)
    addr_start_month = (3003, 1)
    addr_start_nth_weekday = (3004, 1)
    addr_start_weekday = (3005, 1)
    addr_start_minute = (3006, 1)
    addr_end_month = (3007, 1)
    addr_end_nth_weekday = (3008, 1)
    addr_end_weekday = (3009, 1)
    addr_end_minute = (3010, 1)
    addr_summer_time_offset = (3002, 1)
    addr_ntp_setup_access = (3040, 1)
    addr_ntp_ip = (3041, 1)
    addr_sync_mode = (3043, 1)
    addr_sync_period = (3044, 1)
    addr_sync_max_drift = (3045, 1)
    addr_lcd_buzzer_setup_access = (3800, 1)
    addr_lcd_backlight_timeout = (3801, 1)
    addr_lcd_backlight_low_level = (3802, 1)
    addr_buzzer_for_button = (3803, 1)
    ### UINT32 ###
    addr_system_time_sec = (3061, 2)
    addr_system_time_usec = (3063, 2)
    
    addr_reset_demand = (12000, 1)
    addr_reset_demand_peak = (12001, 1)
    addr_demand_sync = (12015, 1)
    
    addr_setup_lock = (2900, 1)
    addr_control_lock = (2901, 1)


class ConfigInitialValue(Enum):
    initial_setup_values = {
        # modbus map - -1 값
        ConfigMap.addr_reset_max_min: None,
        
        # measurement setup - UINT16
        ConfigMap.addr_measurement_setup_access: None,
        ConfigMap.addr_wiring: 0,
        ConfigMap.addr_vt_secondary_ll_voltage: 1900,
        ConfigMap.addr_min_measured_secondary_ln_voltage: 5,
        ConfigMap.addr_reference_voltage_mode: 0,
        ConfigMap.addr_ct_secondary_current: 5,
        ConfigMap.addr_min_measured_current: 5,
        ConfigMap.addr_tdd_reference: 1,
        ConfigMap.addr_demand_sync_mode: 0,
        ConfigMap.addr_num_of_sub_interval: 1,
        ConfigMap.addr_sub_interval_time: 15,
        ConfigMap.addr_thermal_response_index: 90,
        ConfigMap.addr_demand_power_type: 0,
        ConfigMap.addr_phase_power_calculation: 1,
        ConfigMap.addr_total_power_calculation: 0,
        ConfigMap.addr_pf_value_at_no_load: 1,
        ConfigMap.addr_pf_sign: 1,
        ConfigMap.addr_reactive_power_sign: 1,
        # ConfigModbusMap.addr_default_frequency: 1,
        # ConfigModbusMap.addr_max_harmonic_order: 50,
        ConfigMap.addr_rotating_sequence: 1,
        ConfigMap.addr_sliding_reference_voltage_setup_access: None,
        ConfigMap.addr_sliding_reference_voltage_type: 0,
        
        # measurement setup - UINT32
        ConfigMap.addr_reference_voltage: 1900,
        ConfigMap.addr_vt_primary_ll_voltage: 1900,
        ConfigMap.addr_reference_current: 50,
        ConfigMap.addr_ct_primary_current: 50,
        ConfigMap.addr_nominal_tdd_current: 0,
        
        # meter event setup
        ConfigMap.addr_dip_setup_access: None,
        ConfigMap.addr_dip: 0,
        ConfigMap.addr_dip_threshold: 900,
        ConfigMap.addr_dip_hysteresis: 20,
        ConfigMap.addr_3phase_dip_setup_access: None,
        ConfigMap.addr_3phase_dip: 0,
        ConfigMap.addr_swell_setup_access: None,
        ConfigMap.addr_swell: 0,
        ConfigMap.addr_swell_threshold: 1100,
        ConfigMap.addr_swell_hysteresis: 20,
        ConfigMap.addr_semi_event_setup_access: None,
        ConfigMap.addr_semi: 0,
        ConfigMap.addr_itic_event_setup_access: None,
        ConfigMap.addr_itic: 0,
        ConfigMap.addr_iec_event_setup_access: None,
        ConfigMap.addr_iec: 0,
        
        # meter network setup
        ConfigMap.addr_dhcp_setup_access: None,
        ConfigMap.addr_dhcp: 0,
        ConfigMap.addr_rs485_setup_access: None,
        ConfigMap.addr_device_address: 0,
        ConfigMap.addr_bit_rate: 3,
        ConfigMap.addr_parity: 2,
        ConfigMap.addr_stop_bit: 0,
        ConfigMap.addr_modbus_timeout_setup_access: None,
        ConfigMap.addr_modbus_timeout: 600,
        ConfigMap.addr_rstp_setup_access: None,
        ConfigMap.addr_rstp: 0,
        ConfigMap.addr_storm_control_setup_access: None,
        ConfigMap.addr_storm_control: 1,
        ConfigMap.addr_rs485_map_setup_access: None,
        ConfigMap.addr_rs485_map: 0,
        ConfigMap.addr_remote_control_lock_mode_access: None,
        ConfigMap.addr_remote_control_lock_mode: 0,
        
        # meter control
        ConfigMap.addr_meter_test_mode: 0,
        ConfigMap.addr_meter_demo_mode_timeout_setup_access: None,
        ConfigMap.addr_meter_demo_mode_timeout: 60,
        
        # meter system - UINT16
        ConfigMap.addr_description_setup_access: None,
        ConfigMap.addr_installation_year: 1970,
        ConfigMap.addr_installation_month: 1,
        ConfigMap.addr_installation_day: 1,
        ConfigMap.addr_locale_setup_access: None,
        ConfigMap.addr_timezone_offset: 540,
        ConfigMap.addr_temperature_unit: 0,
        ConfigMap.addr_energy_unit: 0,
        ConfigMap.addr_date_display_format: 0,
        ConfigMap.addr_system_time_setup_access: None,
        ConfigMap.addr_summer_time_setup_access: None,
        ConfigMap.addr_summer_time: 0,
        ConfigMap.addr_start_month: 3,
        ConfigMap.addr_start_nth_weekday: 2,
        ConfigMap.addr_start_weekday: 0,
        ConfigMap.addr_start_minute: 120,
        ConfigMap.addr_end_month: 11,
        ConfigMap.addr_end_nth_weekday: 1,
        ConfigMap.addr_end_weekday: 0,
        ConfigMap.addr_end_minute: 120,
        ConfigMap.addr_summer_time_offset: 60,
        ConfigMap.addr_ntp_setup_access: None,
        ConfigMap.addr_ntp_ip: None,
        ConfigMap.addr_sync_mode: 1,
        ConfigMap.addr_sync_period: 600,
        ConfigMap.addr_sync_max_drift: 1,
        ConfigMap.addr_lcd_buzzer_setup_access: None,
        ConfigMap.addr_lcd_backlight_timeout: 300,
        ConfigMap.addr_lcd_backlight_low_level: 10,
        ConfigMap.addr_buzzer_for_button: 1,
        
        # meter system - UINT32
        ConfigMap.addr_system_time_sec: None,
        ConfigMap.addr_system_time_usec: None,
        
        # 기타
        ConfigMap.addr_reset_demand: None,
        ConfigMap.addr_reset_demand_peak: None,
        ConfigMap.addr_demand_sync: None,
        ConfigMap.addr_setup_lock: None,
        ConfigMap.addr_control_lock: None,
    }
