# -*- coding: utf-8 -*-
"""A3700N 전용 터치 좌표 프로파일.

A7300 과 A3700N 은 해상도/UI 레이아웃이 달라 같은 좌표로 눌러도 엉뚱한 곳이
눌리는 경우가 있다. 이 파일은 A3700N 실제 화면 기준으로 좌표를 덮어쓰기
위한 용도.

사용 방식
---------
- 이름은 `config_touch.ConfigTouch` 와 1:1 로 맞춘다.
- `TouchManager` 가 브릿지 경로에서 `ConnectionManager.PRODUCT == "A3700N"`
  일 때 자동으로 A7300 좌표(값) 를 A3700N 좌표로 역조회해 치환한다.
- 이 파일에 없는 이름이 오면 원본(A7300) 좌표를 그대로 사용한다.

초기값은 일단 A7300 과 동일하게 둔다 — 실기 테스트하면서 하나씩 맞춰 넣으면 됨.
예를 들어 Meter 메뉴바가 A3700N 에서 (x, y) 인 걸 확인하면
`touch_main_menu_2 = [x, y]` 로 고쳐넣으면 된다.
"""

from enum import Enum


class ConfigTouchA3700N(Enum):
    ### 상단 메뉴 ###
    touch_main_menu_1 = [100, 85]
    touch_main_menu_2 = [260, 85]   # Meter — 실기 확인 후 조정
    touch_main_menu_3 = [390, 85]
    touch_main_menu_4 = [560, 85]
    touch_main_menu_5 = [720, 85]

    ### 왼쪽 사이드 메뉴 ###
    touch_side_menu_1 = [80, 135]
    touch_side_menu_2 = [80, 180]
    touch_side_menu_3 = [80, 225]
    touch_side_menu_4 = [80, 270]
    touch_side_menu_5 = [80, 315]
    touch_side_menu_6 = [80, 360]
    touch_side_menu_7 = [80, 405]
    touch_side_menu_8 = [80, 450]

    touch_data_view_1 = [320, 210]
    touch_data_view_2 = [620, 210]
    touch_data_view_3 = [320, 280]
    touch_data_view_4 = [620, 280]
    touch_data_view_5 = [320, 360]
    touch_data_view_6 = [620, 360]
    touch_data_view_7 = [320, 430]
    touch_data_view_8 = [620, 430]

    touch_toggle_ll = [410, 150]
    touch_toggle_ln = [510, 150]
    touch_toggle_thd_ll = [520, 150]
    touch_toggle_thd_ln = [620, 150]
    touch_toggle_max = [720, 150]
    touch_toggle_min = [620, 150]
    touch_toggle_phasor_vll = [620, 210]
    touch_toggle_phasor_vln = [720, 210]

    ### phasor, harmonics, waveform 공통 ###
    touch_toggle_analysis_vol = [590, 150]
    touch_toggle_analysis_curr = [720, 150]

    touch_toggle_harmonics_fund = [510, 200]
    touch_dropdown_harmonics_1 = [230, 200]
    touch_dropdown_harmonics_2 = [360, 200]
    touch_toggle_waveform_vol_a = [360, 200]
    touch_toggle_waveform_vol_b = [430, 200]
    touch_toggle_waveform_vol_c = [490, 200]

    ### harmonics a,b,c 와 공통 ###
    touch_toggle_waveform_curr_a = [620, 200]
    touch_toggle_waveform_curr_b = [680, 200]
    touch_toggle_waveform_curr_c = [740, 200]

    ### harmonics dropdown menu 선택지 ###
    touch_harmonics_sub_v = [230, 240]
    touch_harmonics_sub_fund = [230, 285]
    touch_harmonics_sub_rms = [230, 330]
    touch_harmonics_sub_graph = [360, 240]
    touch_harmonics_sub_text = [360, 285]

    ### popup button ###
    touch_btn_apply = [620, 150]
    touch_btn_cancel = [720, 150]
    touch_btn_popup_enter = [340, 425]
    touch_btn_popup_cancel = [450, 425]
    touch_btn_popup_1 = [400, 110]
    touch_btn_popup_2 = [400, 160]
    touch_btn_popup_3 = [400, 215]
    touch_btn_popup_4 = [400, 265]
    touch_btn_popup_5 = [400, 315]
    touch_btn_popup_wide_1 = [270, 105]
    touch_btn_popup_wide_2 = [530, 105]
    touch_btn_popup_wide_3 = [270, 155]
    touch_btn_popup_wide_4 = [530, 155]
    touch_btn_popup_wide_5 = [270, 205]
    touch_btn_popup_wide_6 = [530, 205]
    touch_btn_popup_wide_7 = [270, 260]
    touch_btn_popup_wide_8 = [530, 260]
    touch_btn_popup_wide_9 = [270, 315]
    touch_btn_popup_wide_10 = [530, 315]
    touch_btn_popup_wide_11 = [270, 365]
    touch_btn_popup_wide_12 = [530, 365]

    ### popup number, enter/cancel 은 위 popup button 와 공유 ###
    touch_btn_number_1 = [310, 200]
    touch_btn_number_2 = [370, 200]
    touch_btn_number_3 = [430, 200]
    touch_btn_number_4 = [310, 255]
    touch_btn_number_5 = [370, 255]
    touch_btn_number_6 = [430, 255]
    touch_btn_number_7 = [310, 310]
    touch_btn_number_8 = [370, 310]
    touch_btn_number_9 = [430, 310]
    touch_btn_number_0 = [310, 370]
    touch_btn_number_dot = [370, 370]
    touch_btn_number_minus = [430, 370]
    touch_btn_number_back = [490, 225]
    touch_btn_number_clear = [485, 340]

    ### Primary Reference Voltage popup ###
    touch_btn_ref_ll = [330, 100]
    touch_btn_ref_ln = [470, 100]
    touch_btn_ref_num_1 = [285, 250]
    touch_btn_ref_num_2 = [345, 250]
    touch_btn_ref_num_3 = [400, 250]
    touch_btn_ref_num_4 = [455, 250]
    touch_btn_ref_num_5 = [285, 310]
    touch_btn_ref_num_6 = [345, 310]
    touch_btn_ref_num_7 = [400, 310]
    touch_btn_ref_num_8 = [455, 310]
    touch_btn_ref_num_9 = [285, 365]
    touch_btn_ref_num_0 = [345, 365]

    ### TDD Nominal Current popup ###
    touch_btn_tdd_enter = [340, 400]
    touch_btn_tdd_cancel = [460, 400]
    touch_btn_tdd_ref_curr = [490, 120]
    touch_btn_tdd_num_1 = [285, 220]
    touch_btn_tdd_num_2 = [345, 220]
    touch_btn_tdd_num_3 = [400, 220]
    touch_btn_tdd_num_4 = [460, 220]
    touch_btn_tdd_num_5 = [285, 280]
    touch_btn_tdd_num_6 = [345, 280]
    touch_btn_tdd_num_7 = [400, 280]
    touch_btn_tdd_num_8 = [460, 280]
    touch_btn_tdd_num_9 = [285, 335]
    touch_btn_tdd_num_0 = [345, 335]

    ### 위아래 스크롤 ###
    touch_btn_scroll_down = [750, 450]
    touch_btn_scroll_up = [750, 200]
