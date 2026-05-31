import re
import cv2
from datetime import datetime, timezone, timedelta
import shutil
import os
import glob
import pandas as pd
from collections import Counter
import time

from function.func_ocr import PaddleOCRManager
from function.func_connection import ConnectionManager
from function.func_modbus import ModbusLabels

from config.a7300 import Configs, ConfigMap

class Evaluation:

    reset_time = None
    ocr_manager = PaddleOCRManager()
    config_data = Configs()
    rois = config_data.roi_params()
    connect_manager = ConnectionManager()
    modbus_labels = ModbusLabels()

    def __init__(self):
        pass


    def load_image_file(self, search_pattern, start_time, retries=3, delay=1):
        if not start_time:
            print("Error: 기준 시간을 장치에서 읽어오지 못했습니다.")
            return None
        print(f"기준 시간: {start_time.strftime('%Y%m%d_%H%M%S')}")
        time_margin = timedelta(seconds=5)
        start_time = start_time - time_margin
    
        for attempt in range(retries):
            candidate_files = []
            all_files = glob.glob(search_pattern, recursive=True)

            for file_path in all_files:
                filename = os.path.basename(file_path)
                match = re.search(r'(\d{8}_\d{6})', filename)
                if not match:
                    continue
                
                try:
                    timestamp_str = match.group(1)
                    file_time = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                    # print(f"파일 시간: {file_time}")
                    
                    if file_time > start_time:
                        candidate_files.append((file_time, file_path))
                except ValueError:
                    continue

            if candidate_files:
                candidate_files.sort()
                latest_image_path = candidate_files[0][1]
                
                normalized_path = os.path.normpath(latest_image_path)
                print("찾은 파일:", normalized_path)
                return normalized_path

            if attempt < retries - 1:
                print(f"파일을 찾지 못했습니다. {delay}초 후 다시 시도합니다... (시도 {attempt + 1}/{retries})")
                time.sleep(delay)

        print(f"경고: {retries}번 시도 후에도 새 파일을 찾지 못했습니다.")
        return None

    ### With Demo Balance ###
    def eval_test_mode_balance(self, ocr_res, correct_answers, modbus_meas_value, meas_rules, ratio_rules, reset_time=None, modbus_timestamp_value=None, image_path=None):
        self.demo_test_result = False
        self.measurement_error = False
        self.condition_met = False

        ocr_res = ocr_res or []
        meas_rules = meas_rules or []
        ratio_rules = ratio_rules or []
        modbus_meas_value = modbus_meas_value or []
        
        image = cv2.imread(image_path)

        def validate_ratio(percent_list, rules_list):
            results_list = []
            percent_error = False

            if len(percent_list) != len(rules_list):
                print(f"FAIL - Mismatch between number of ratio and rules.")
                return True, ["Length mismatch"]

            for item, rules in zip(percent_list, rules_list):
                match = re.match(r"([-+]?\d+\.?\d*)\s*(.*)", item)

                if 'text' in rules:
                    ocr_text = item.strip()
                    expected_text = rules['text']
                    if ocr_text == expected_text:
                        result_str = f"'{ocr_text}' vs '{expected_text}' -> PASS"
                        results_list.append(result_str)
                        print(result_str)
                    else:
                        result_str = f"'{ocr_text}' vs '{expected_text}' -> FAIL"
                        percent_error = True
                        results_list.append(result_str)
                        print(result_str)

                elif match and match.group(1):
                    numeric_value = float(match.group(1))
                    unit = match.group(2).strip()

                    lower_limit = rules['low']
                    upper_limit = rules['high']
                    right_unit = rules['unit']

                    if lower_limit <= numeric_value <= upper_limit and unit == right_unit:
                        print(f"'{item}' -> PASS")
                        result = f"{item} -> PASS"
                        results_list.append(result)
                    
                    else:
                        print(f"'{item}' -> (FAIL / 단위 또는 범위 오류)")
                        percent_error = True
                        result = f"{item} -> FAIL"
                        results_list.append(result)
                else:
                    print(f"'{item}' -> (INFO - Skipping non-numeric text)")
            
            return percent_error, results_list
        
        def validate_timestamp(timestamp_list, reset_time):
            timestamp_error = False
            results_list = []
            numeric_list = []
            reset_timestamp = reset_time.timestamp()
            print(reset_time)

            for item in timestamp_list:
                naive_dt_object = datetime.strptime(item, '%Y-%m-%d %H:%M:%S')
                utc_dt_object = naive_dt_object.replace(tzinfo=timezone.utc)
                unix_timestamp = utc_dt_object.timestamp()

                if reset_timestamp - 30 < unix_timestamp < reset_timestamp + 30:
                    print(f"'{item}' -> PASS")
                    result = f"{item} -> PASS"
                    results_list.append(result)
                    numeric_list.append(unix_timestamp)
                else:
                    print(f"'{item}' -> (FAIL - 단위 또는 범위 오류)")
                    timestamp_error = True
                    result = f"{item} -> FAIL"
                    results_list.append(result)
                    numeric_list.append(unix_timestamp)
            
            return timestamp_error, results_list, numeric_list
        
        def validate_measurement(measurement_list, rules_list):
            results_list = []
            numeric_list = []

            if len(measurement_list) != len(rules_list):
                print(f"FAIL - Mismatch between number of measurements and rules.")
                print(measurement_list, rules_list)
                return True, ["Length mismatch"], []

            for item, rules in zip(measurement_list, rules_list):
                match = re.match(r"([-+]?\d+\.?\d*)\s*(.*)", item)
                if match and match.group(1):
                    numeric_value = float(match.group(1))
                    unit = match.group(2).strip()

                    # 해당 항목에 맞는 개별 규칙을 가져옵니다.
                    lower_limit = rules['low']
                    upper_limit = rules['high']

                    if 'unit' in rules:
                        right_unit = rules['unit']
                        if lower_limit <= numeric_value <= upper_limit and unit == right_unit:
                            result = f"'{item}' -> PASS"
                            results_list.append(result)
                            numeric_list.append(numeric_value)
                        else:
                            result = f"'{item}' -> (FAIL)"
                            results_list.append(result)
                            self.measurement_error = True
                            numeric_list.append(numeric_value)
                    else:
                        if lower_limit <= numeric_value <= upper_limit:
                            result = f"'{item}' -> PASS"
                            results_list.append(result)
                            numeric_list.append(numeric_value)
                        else:
                            result = f"'{item}' -> (FAIL)"
                            results_list.append(result)
                            self.measurement_error = True
                            numeric_list.append(numeric_value)
            
            return self.measurement_error, results_list, numeric_list
        
        def validate_modbus(modbus_value, right_value, tolerance=0.5):
            formatted_value = []
            modbus_results = []
            modbus_error = False

            for item in modbus_value:
                value = abs(item)
                if value >= 1000:
                    value = value / 1000

                if round(value, 1) >= 100:
                    for_value = f'{value:.1f}'
                    formatted_value.append(for_value)
                elif round(value, 2) >= 10:
                    for_value = f'{value:.2f}'
                    formatted_value.append(for_value)
                elif round(value, 3) >= 1:
                    for_value = f'{value:.3f}'
                    formatted_value.append(for_value)
                else:
                    for_value = f'{value:.3f}'
                    formatted_value.append(for_value)

            for modbus_val, ocr_val in zip(formatted_value, right_value):
        
                if modbus_val is None or ocr_val is None:
                    result_str = f"Modbus: {modbus_val}, OCR: {ocr_val} -> FAIL (Invalid value)"
                    print("len(mobus_val) != len(ocr_val)")
                    continue
                
                modbus_val = float(modbus_val)
                ocr_val = float(ocr_val)

                difference = abs(modbus_val) - abs(ocr_val)
                abs_difference = abs(difference)
                if abs_difference <= tolerance:
                    result_str = f"Modbus: {modbus_val:.3f}, OCR: {ocr_val:.3f} -> PASS (Diff: {abs_difference:.3f})"
                    modbus_results.append(result_str)
                    print(f"{result_str}")
                else:
                    result_str = f"Modbus: {modbus_val:.3f}, OCR: {ocr_val:.3f} -> FAIL (Diff: {abs_difference:.3f})"
                    modbus_results.append(result_str)
                    print(f"{result_str}")
                    modbus_error = True

            return modbus_error, formatted_value, modbus_results

        ### 고정 문자 가공 ###
        UNITS = {"V", "kW", "A", "kVAR", "kVA", "%", "Hz"}
        PHASE_SKIP = False
        PERCENT_AS_RATIO = False


        ocr_fixed_text = []
        ocr_measurement_text = []
        ocr_ratio_text = []
        ocr_timestamp_text = []
        ocr_unit_text = []

        numeric_positions = []   # (index, "24.85")
        unit_positions = []      # (index, "A")

        ocr_exp_results = {
            "unmatched_numbers": [],   # 단위 못 붙인 숫자
            "unmatched_units": [],     # 숫자 못 찾은 단위(남는 단위)
        }

        for idx, result in enumerate(ocr_res):
            text = result.strip()
            if not text:
                continue

            # 1) TimeStamp
            if re.search(r'\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}', text):
                ocr_timestamp_text.append(text)
                continue
            
            # 2) 비율
            if re.fullmatch(r'\d+(?:\.\d+)?\s*%', text):
                ocr_ratio_text.append(text)
                PERCENT_AS_RATIO = True
                continue

            if ratio_rules:
                RATIO_TEXTS = {r.get("text") for r in ratio_rules if isinstance(r, dict) and r.get("text")}
                if text in RATIO_TEXTS:
                    ocr_ratio_text.append(text)
                    continue

            # 3) 단위만 단독으로 있는 경우 (V, A, kW, Hz, …)
            try:
                _ = float(text.replace(',', ''))
                numeric_positions.append((idx, text))
                PHASE_SKIP = True
                continue
            except ValueError:
                pass

            if text in UNITS:
                if text == "%":
                    unit_positions.append((idx, text))
                    continue
                if PHASE_SKIP:
                    unit_positions.append((idx, text))
                else:
                    ocr_fixed_text.append(text)
                continue

            # 5) 나머지는 고정 텍스트
            ocr_fixed_text.append(text)

        # -----------------------------
        # 숫자와 단위 매칭 단계
        # -----------------------------

        used_n_idxs = set()
        used_u_idxs = set()

        meas_pairs = []   # (n_i, "190.6 V", "V")
        ratio_pairs = []  # (n_i, "43.2 %")

        # (1) 단위가 아예 없는 화면이면 -> 숫자 전부 measurement로 (단위="")
        if len(unit_positions) == 0:
            for n_i, n_val in numeric_positions:
                meas_pairs.append((n_i, n_val, ""))

        else:
            # (2) 단위가 있는 화면이면 -> "가까운 이전 숫자"만 매칭 (B zip 매칭 X)
            for u_i, u_val in unit_positions:
                candidates = [n for n in numeric_positions if n[0] < u_i and n[0] not in used_n_idxs]
                if not candidates:
                    continue

                n_i, n_val = candidates[-1]

                # n_i~u_i 사이에 다른 숫자가 있으면 짝꿍 아니라고 판단(기존 너 로직 유지)
                if any(n_i < other_i < u_i and other_i not in used_n_idxs for other_i, _ in numeric_positions):
                    continue

                used_n_idxs.add(n_i)
                used_u_idxs.add(u_i)

                if u_val == "%":
                    if PERCENT_AS_RATIO:
                        ratio_pairs.append((n_i, f"{n_val} %"))
                    else:
                        meas_pairs.append((n_i, f"{n_val} {u_val}", u_val))
                else:
                    meas_pairs.append((n_i, f"{n_val} {u_val}", u_val))

            # (3) 남는 숫자/단위는 exp로만 기록
            rem_nums  = [(i, val) for i, val in numeric_positions if i not in used_n_idxs]
            rem_units = [(i, val) for i, val in unit_positions   if i not in used_u_idxs]

            ocr_exp_results["unmatched_numbers"] = [val for _, val in rem_nums]
            ocr_exp_results["unmatched_units"]   = [val for _, val in rem_units]

        # 최종 정렬(인덱스 기준)
        meas_pairs.sort(key=lambda x: x[0])
        ocr_measurement_text = [p[1] for p in meas_pairs]
        ocr_unit_text = [p[2] for p in meas_pairs]

        ratio_pairs.sort(key=lambda x: x[0])
        ocr_ratio_text.extend([p[1] for p in ratio_pairs])


        # 디버깅용 출력
        print("FIXED :", ocr_fixed_text)
        print("MEAS  :", ocr_measurement_text)
        print("RATIO :", ocr_ratio_text)
        print("TIME  :", ocr_timestamp_text)
        print("Exp   :", ocr_exp_results)
        print("nums:", numeric_positions)
        print("units:", unit_positions)
        ####################

        ### 고정 문자 중 잘못된 문자 검증 ###
        ocr_fixed_text_counter = Counter(ocr_fixed_text)
        correct_answers_counter = Counter(correct_answers)

        ocr_error = list((ocr_fixed_text_counter - correct_answers_counter).elements())
        ocr_missing_item = list((correct_answers_counter - ocr_fixed_text_counter).elements())
        ####################
        
        all_meas_results = []
        all_modbus_results = []
        ratio_results = []
        timestamp_results = []
        meas_results = []
        meas_modbus_results = []

        ### 검사
        if ocr_ratio_text and ocr_timestamp_text:
            ratio_error, ratio_results = validate_ratio(ocr_ratio_text, ratio_rules)
            all_meas_results.append(ratio_error)
            timestamp_error, timestamp_results, timestamp_numeric_list = validate_timestamp(ocr_timestamp_text, reset_time)
            all_meas_results.append(timestamp_error)
            meas_error, meas_results, meas_numeric_list = validate_measurement(ocr_measurement_text, meas_rules)
            all_meas_results.append(meas_error)
            print(modbus_meas_value)
            meas_modbus_error, mea_modbus_raw_value, meas_modbus_results = validate_modbus(modbus_meas_value, meas_numeric_list)
            all_modbus_results.append(meas_modbus_error)

        elif ocr_ratio_text and not ocr_timestamp_text:
            ratio_error, ratio_results = validate_ratio(ocr_ratio_text, ratio_rules)
            print(ocr_ratio_text, ratio_results)
            all_meas_results.append(ratio_error)
            meas_error, meas_results, meas_numeric_list = validate_measurement(ocr_measurement_text, meas_rules)
            all_meas_results.append(meas_error)
            print(modbus_meas_value)
            meas_modbus_error, mea_modbus_raw_value, meas_modbus_results = validate_modbus(modbus_meas_value, meas_numeric_list)
            all_modbus_results.append(meas_modbus_error)

        elif not ocr_ratio_text and ocr_timestamp_text:
            timestamp_error, timestamp_results, timestamp_numeric_list = validate_timestamp(ocr_timestamp_text, reset_time)
            all_meas_results.append(timestamp_error)
            meas_error, meas_results, meas_numeric_list = validate_measurement(ocr_measurement_text, meas_rules)
            all_meas_results.append(meas_error)
            print(modbus_meas_value)
            meas_modbus_error, mea_modbus_raw_value, meas_modbus_results = validate_modbus(modbus_meas_value, meas_numeric_list)
            all_modbus_results.append(meas_modbus_error)
        
        elif not ocr_ratio_text and not ocr_timestamp_text:
            meas_error, meas_results, meas_numeric_list = validate_measurement(ocr_measurement_text, meas_rules)
            all_meas_results.append(meas_error)
            print(modbus_meas_value)
            meas_modbus_error, mea_modbus_raw_value, meas_modbus_results = validate_modbus(modbus_meas_value, meas_numeric_list)
            all_modbus_results.append(meas_modbus_error)
        
        elif not self.condition_met:
            print("Nothing matching word")

        for item in all_meas_results:
            if item == True:
                self.demo_test_result = True
        
        for item in all_modbus_results:
            if item == True:
                self.demo_test_result = True

        print(f"OCR - 정답: {ocr_error}")
        print(f"정답 - OCR: {ocr_missing_item}")

        return self.demo_test_result, ocr_error, ocr_missing_item, ocr_fixed_text, ratio_results, timestamp_results, meas_results, meas_modbus_results, ocr_ratio_text, ocr_exp_results
    
    def test_mode_save_csv(self, base_save_path, img_path, ocr_fixed_text, ocr_error, right_error, meas_modbus_results, reset_time, test_result=False, ocr_meas_ratio=None, ocr_meas_timestamp=None, ocr_measurement=None, ocr_ratio_raw=None, ocr_exp_results=None):
        """
        img_path: 이미지경로 + 이미지파일 제목 -> csv 파일 제목이 됨
        base_save_path: CSV/이미지 저장할 폴더
        img_path:   원본 이미지 파일 경로
        ocr_fixed_text: str, 고정 문자
        
        """

        if test_result or ocr_error or right_error:
            overall_result = "FAIL"
        else:
            overall_result = "PASS"
            
        results_dict = {
                        "Data View Fixed text": str(ocr_fixed_text),
                        "OCR Errors (Extra)": f"{ocr_error} ({'FAIL' if ocr_error else 'PASS'})",
                        "OCR Errors (Missing)": f"{right_error} ({'FAIL' if right_error else 'PASS'})",
                        "Meas Ratio Results": str(ocr_meas_ratio),
                        "OCR Ratio Raw": str(ocr_ratio_raw),
                        "Timestamp Results": f"{str(ocr_meas_timestamp)} / Timestamp Standard: {str(reset_time)}",
                        "Measurement Results": str(ocr_measurement),
                        "Modbus Measurement": str(meas_modbus_results),
                        "Exp Results": str(ocr_exp_results),
                        }

        df = pd.DataFrame(list(results_dict.items()), columns=['Parameter', 'Value'])

        # Saving the CSV
        file_name_with_extension = os.path.basename(img_path)
        ip_to_remove = f"{self.connect_manager.SERVER_IP}_"
        if file_name_with_extension.startswith(ip_to_remove):
            file_name_without_ip = file_name_with_extension[len(ip_to_remove):]
        else:
            file_name_without_ip = file_name_with_extension

        image_file_name = os.path.splitext(file_name_without_ip)[0]
        
        save_path = os.path.join(base_save_path, f"{overall_result}_ocr_{image_file_name}.csv")

        df.to_csv(save_path, index=False)
        dest_image_path = os.path.join(base_save_path, file_name_without_ip)
        shutil.copy(img_path, dest_image_path)
