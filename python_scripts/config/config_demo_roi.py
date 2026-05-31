from enum import Enum

class ConfigROI(Enum):

    m_all_area = []

    m_vol_rms_ll_fixed_text = ['RMS Voltage', 'L-L', 'L-N', 'Min', 'Max', 'AB', 'BC', 'CA', 'Average']
    m_vol_rms_ln_fixed_text = ['RMS Voltage', 'L-L', 'L-N', 'Min', 'Max', 'A', 'B', 'C', 'Average']
    m_vol_fund_ll_fixed_text = ['Fund. Volt.', 'L-L', 'L-N', 'Min', 'Max', 'AB', 'BC', 'CA', 'Average']
    m_vol_fund_ln_fixed_text = ['Fund. Volt.', 'L-L', 'L-N', 'Min', 'Max', 'A', 'B', 'C', 'Average']
    m_vol_thd_ll_fixed_text = ['Total Harmonic Distortion', 'L-L', 'L-N', 'Max', 'AB', 'BC', 'CA']
    m_vol_thd_ln_fixed_text = ['Total Harmonic Distortion', 'L-L', 'L-N', 'Max', 'A', 'B', 'C']
    m_vol_freq_fixed_text = ['Frequency', 'Min', 'Max', 'Frequency']
    m_vol_residual_fixed_text = ['Residual Voltage', 'Min', 'Max', 'RMS', 'Fund.']
    m_curr_rms_fixed_text = ['RMS Current', 'Min', 'Max', 'A', 'B', 'C', 'Average']
    m_curr_fund_fixed_text = ['Fundamental Current', 'Min', 'Max', 'A', 'B', 'C', 'Average']
    m_curr_demand_fixed_text = ['Demand Current', 'Peak', 'A', 'B', 'C', 'Average']
    m_curr_thd_fixed_text = ['Total Harmonic Distortion', 'Max', 'A', 'B', 'C']
    m_curr_tdd_fixed_text = ['Total Demand Distortion', 'Max', 'A', 'B', 'C']
    m_curr_cf_fixed_text = ['Crest Factor', 'Max', 'A', 'B', 'C']
    m_curr_kf_fixed_text = ['K-Factor', 'Max', 'A', 'B', 'C']
    m_curr_residual_fixed_text = ['Residual Current', 'Min', 'Max', 'RMS', 'Fund.']
    m_pow_p_fixed_text = ['Active Power', 'Min', 'Max', 'A', 'B', 'C', 'Total']
    m_pow_q_fixed_text = ['Reactive Power', 'Min', 'Max', 'A', 'B', 'C', 'Total']
    m_pow_s_fixed_text = ['Apparent Power', 'Min', 'Max', 'A', 'B', 'C', 'Total']
    m_pow_pf_fixed_text = ['Power Factor', 'Min', 'Max', 'A', 'B', 'C', 'Total']
    m_pow_demand_fixed_text = ['Demand Active Power', 'Peak', 'A', 'B', 'C', 'Total']
    m_pow_energy_fixed_text = ['Energy', 'Active', 'Reactive', 'Apparent', 'Received', 'Delivered', 'Sum', 'Net']

    m_anal_vol_symm_ll_fixed_text = ['Volt. Symm. Component', 'L-L', 'L-N', 'Max', 'Positive-', 'Sequence', 'Negative-', 'Sequence']
    m_anal_vol_symm_ln_fixed_text = ['Volt. Symm. Component', 'L-L', 'L-N', 'Max', 'Positive-', 'Sequence', 'Negative-', 'Sequence', 'Zero-', 'Sequence']
    m_anal_vol_unbal_fixed_text = ['Voltage Unbalance', 'Max', 'NEMA', 'NEMA', 'Negative-', 'Sequence', 'Zero-', 'Sequence']
    m_anal_curr_symm_fixed_text = ['Curr. Symm. Component', 'Max', 'Positive-', 'Sequence', 'Negative-', 'Sequence', 'Zero-', 'Sequence']
    m_anal_curr_unbal_fixed_text = ['Current Unbalance', 'Max', 'NEMA', 'Negative-', 'Sequence', 'Zero-', 'Sequence']

    test_mode_balance_title = ['title']
    test_mode_balance_phase = ['a,b,c']
    test_mode_balance_ratio = ['50.0 %'] # +timestamp
    test_mode_balance_meas = ['25.00 A']
    tmb_title_residual_1 = ['residual']
    tmb_title_residual_2 = ['min max']

class Configs():

    def __init__(self) -> None:
        self.roi_map = {}

    def roi_params(self):

        self.view0_zone_1 = (160, 120, 630, 350)

        self.roi_map[ConfigROI.m_all_area] = self.view0_zone_1