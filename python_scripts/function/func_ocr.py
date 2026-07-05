import cv2
import os
import sys

from pathlib import Path
from ultralytics import YOLO
from paddleocr import PaddleOCR
import numpy as np

import paddle.base.libpaddle as _libpaddle
if not hasattr(_libpaddle.AnalysisConfig, 'set_optimization_level'):
    _libpaddle.AnalysisConfig.set_optimization_level = lambda self, level: None


class YoloManager:

    def __init__(self) -> None:
        if getattr(sys, "frozen", False):
            self.BASE_DIR = Path(sys.executable).resolve().parent
        else:
            self.BASE_DIR = Path(__file__).resolve().parent

        # [MERGED] VisionPython: "test_best.pt" / VisionOCR: "new_best.pt"
        # VisionOCR 환경에 맞춰 "new_best.pt" 사용. 필요시 변경.
        self.MODEL_PATH = self.BASE_DIR / "yolov11_model" / "det" / "test_best.pt"
        self.model = YOLO(self.MODEL_PATH)

    def _yolo_settings(self, product):
        settings = {
            "roi": (160, 120, 790, 470),
            "conf": 0.3,
            "iou": 0.2,
            "augment": True,
            "inclusion_th": 0.80,
            "nested_strategy": "drop_inner",
            "outer_min_inner_count": 2,
            "outer_min_width": 120,
            "outer_max_height": 80,
            "outer_max_y2": None,
            "wide_noise_min_width_ratio": None,
            "wide_noise_max_height": 80,
            "wide_noise_max_conf": 0.70,
        }
        product_settings = {
            "A2700": {
                "roi": (135, 90, 780, 425),
            },
            "A7300": {
                "nested_strategy": "drop_outer_multi_inner",
                "outer_min_inner_count": 1,
                "outer_min_width": 65,
                "outer_max_y2": 125,
                "wide_noise_min_width_ratio": 0.85,
            },
        }
        settings.update(product_settings.get(product, {}))
        return settings

    def _merge_adjacent_boxes(self, boxes, x_tolerance=-8, y_tolerance=10):
        """
        같은 줄(y_tolerance 이내)에 있고, x 거리(box.x1 - last_box.x2)가
        x_tolerance 이하인 박스들을 하나의 큰 박스로 병합합니다.

        x_tolerance 의미:
            -8  : 8px 이상 겹친 경우만 합침 (기본). raw 박스 padding(+2/+6)
                보정용. 진짜로 겹친 49.7+% 같은 토큰은 잡지만, padding 때문에
                살짝 닿은 것처럼 보이는 다른 박스는 분리.
            <0  : 음수 절댓값만큼 겹쳐야 합침.
            0   : 닿거나 겹친 경우만 합침 (padding 보정 X — 의도치 않은 합침 위험).
            >0  : 그 px 이내로 떨어져 있어도 합침.
        """
        if not boxes:
            return []
        # 1. 위에서 아래로, 왼쪽에서 오른쪽으로 정렬.
        #    y 정렬 키를 y_tolerance 단위로 양자화 → 같은 행 박스가 y 미세
        #    차이(예: 95 vs 100)가 있어도 같은 그룹에 묶여 x 순으로 정렬됨.
        sorted_boxes = sorted(
            boxes,
            key=lambda b: (((b[1] + b[3]) / 2) // y_tolerance, b[0]),
        )
        merged_boxes = []
        for box in sorted_boxes:
            if not merged_boxes:
                merged_boxes.append(box)
                continue
            last_box = merged_boxes[-1]

            # 박스 중앙 y좌표 계산
            cy_last = (last_box[1] + last_box[3]) / 2
            cy_current = (box[1] + box[3]) / 2
            # 같은 줄에 있는지 확인
            if abs(cy_last - cy_current) <= y_tolerance:
                # 앞 박스의 끝(x2)과 뒷 박스의 시작(x1) 사이의 거리 계산
                # 겹쳐있으면 음수가 나오고, 떨어져 있으면 양수가 나옵니다.
                dist_x = box[0] - last_box[2]

                # 음수 하한: 직전 박스 너비 만큼만 "겹침" 으로 인정. 그 이상
                # 큰 음수는 정렬 키 차이로 우연히 다음에 정렬된 무관한 위치의
                # 박스 (예: timestamp 가 % 다음 정렬되어 dist_x=-400 같이
                # 행 폭만큼 음수로 계산되는 케이스) 를 막는다.
                min_overlap = -(last_box[2] - last_box[0])

                # 거리가 [min_overlap, x_tolerance] 범위면 병합.
                if min_overlap <= dist_x <= x_tolerance:
                    new_x1 = min(last_box[0], box[0])
                    new_y1 = min(last_box[1], box[1])
                    new_x2 = max(last_box[2], box[2])
                    new_y2 = max(last_box[3], box[3])
                    new_area = (new_x2 - new_x1) * (new_y2 - new_y1)
                    # Confidence는 둘 중 높은 것으로 유지
                    new_conf = max(last_box[5], box[5])

                    # 마지막 박스를 병합된 큰 박스로 교체
                    merged_boxes[-1] = [new_x1, new_y1, new_x2, new_y2, new_area, new_conf, last_box[6]]
                    continue
            # 병합 조건에 맞지 않으면 그냥 새 박스로 추가
            merged_boxes.append(box)
        return merged_boxes

    def yolo_basic(self, image_path, return_boxes=False):

        cropped_images_list = []
        detected_names = []
        boxes_list = []

        frame = cv2.imread(image_path)
        if frame is None:
            print(f"이미지를 읽을 수 없습니다. 경로를 확인해주세요: {image_path}")
            if return_boxes:
                return [], [], []
            return [], []
        
        # 제품별 outer crop — A7300/A3700N 은 기본값, A2700 은 화면 chrome 위치가
        # 다르므로 별도 좌표 사용. 새 제품 추가 시 여기서 분기.
        from function.func_connection import ConnectionManager  # 지연 import (순환 회피)
        _product = ConnectionManager().PRODUCT
        settings = self._yolo_settings(_product)
        roi_x1, roi_y1, roi_x2, roi_y2 = settings["roi"]
        roi = frame[roi_y1:roi_y2, roi_x1:roi_x2]

        gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        
        # YOLO는 무조건 3채널(RGB) 구조를 요구하므로 형태만 맞춰줍니다.
        # (시각적으로는 흑백이지만 데이터 형태는 3채널)
        roi_for_yolo = cv2.cvtColor(gray_roi, cv2.COLOR_GRAY2BGR)

        # __init__ 에서 로드한 모델 재사용 — 호출마다 재로드하면 매번
        # 모델 파일을 다시 읽어 수 초씩 낭비된다.
        model = self.model

        # results = model(roi, conf=0.3, iou=0.2)
        results = model(
            roi_for_yolo,
            conf=settings["conf"],
            iou=settings["iou"],
            augment=settings["augment"],
        )
        result = results[0]

        h, w, _ = roi_for_yolo.shape
        
        # 박스 그리기 반복문
        copy_frame = roi_for_yolo.copy()
        for i, box in enumerate(result.boxes):

            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        
            # 이미지 밖으로 나가지 않게 클램핑 (안전장치)
            x1 = max(0, x1 - 2)
            y1 = max(0, y1 + 2)
            x2 = min(w, x2 + 2)
            y2 = min(h, y2 + 12)

            cls_id = int(box.cls[0])
            name = result.names[cls_id]
            conf = float(box.conf[0])
        
            print(f"Object {i}: {name} -> Box: [{x1}, {y1}, {x2}, {y2}]")

            cv2.rectangle(copy_frame, (x1, y1), (x2, y2), (0, 0, 255), 1)

            label = f"{name} {conf:.2f}"
            cv2.putText(copy_frame, label, (x1, y1 - 5), cv2.FONT_ITALIC, 0.5, (0, 0, 0), 1)

        # 최종 확인 창은 아래의 제품별 nested-box 후처리 이후 박스를 그린다.

        raw = []
        for box in result.boxes:
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            conf = float(box.conf[0])
            cls_id = int(box.cls[0])
            name = result.names[cls_id]

            # if (y2 - y1) > 40:
            #     # YOLO 박스 좌표가 roi 기준이므로 roi를 넘겨줌
            #     x1, y1, x2, y2 = self._shrink_box_to_text(roi, x1, y1, x2, y2)
            # else:
            # 정상적인 글자 크기면 기존에 세팅하신 패딩 유지
            x1 = max(0, x1 - 2)
            y1 = max(0, y1 + 1)
            x2 = min(w, x2 + 6)
            y2 = min(h, y2 + 13)

            area = max(1, (x2 - x1) * (y2 - y1))
            raw.append([x1, y1, x2, y2, area, conf, name])

        keep = [True] * len(raw)
        # nested 박스 처리.
        # 기본/A2700: 작은 박스 j 가 큰 박스 i 에 inclusion_th 이상 들어가면 j 제거.
        # A7300: 큰 박스 하나가 여러 작은 텍스트 박스를 감싸면 큰 박스를 제거.
        # IoU 가 아니라 "작은 박스 면적 기준 포함 비율" — IoU NMS 가 흘려버리는
        # nested 박스(예: "Line-to-Line, 380" 안에 또 잡힌 "380")를 잡기 위함.
        # 임계값: 80% 부터 시작. 떨어지는 케이스 있으면 0.7 까지, 과제거되면 0.9.
        inclusion_th = settings["inclusion_th"]
        nested_strategy = settings["nested_strategy"]

        for i in range(len(raw)):
            if not keep[i]:
                continue
            xi1, yi1, xi2, yi2, ai, ci, ni = raw[i]
            contained = []

            for j in range(len(raw)):
                if i == j or not keep[j]:
                    continue
                xj1, yj1, xj2, yj2, aj, cj, nj = raw[j]

                # i ∩ j 면적 계산
                ix1 = max(xi1, xj1); iy1 = max(yi1, yj1)
                ix2 = min(xi2, xj2); iy2 = min(yi2, yj2)
                if ix1 >= ix2 or iy1 >= iy2:
                    continue  # 안 겹침
                inter = (ix2 - ix1) * (iy2 - iy1)

                print(f"[nested] i={i}({xi1},{yi1},{xi2},{yi2}) j={j}({xj1},{yj1},{xj2},{yj2}) inter/aj={inter/aj:.2f} ai>aj={ai>aj}")

                if ai > aj and inter / aj >= inclusion_th:
                    contained.append(j)
                    if nested_strategy == "drop_inner":
                        keep[j] = False

            if nested_strategy == "drop_outer_multi_inner":
                width = xi2 - xi1
                height = yi2 - yi1
                outer_max_y2 = settings["outer_max_y2"]
                if (
                    len(contained) >= settings["outer_min_inner_count"]
                    and width >= settings["outer_min_width"]
                    and height <= settings["outer_max_height"]
                    and (outer_max_y2 is None or yi2 <= outer_max_y2)
                ):
                    print(
                        f"[nested] drop outer box for {_product}: "
                        f"i={i} inner_count={len(contained)} "
                        f"box=({xi1},{yi1},{xi2},{yi2})"
                    )
                    keep[i] = False

        # A7300 can occasionally classify a full table row or horizontal rule as
        # one huge "text" box. It is much wider than real labels/values and
        # carries low confidence, so remove it before OCR cropping.
        wide_noise_ratio = settings.get("wide_noise_min_width_ratio")
        if wide_noise_ratio is not None:
            min_width = w * wide_noise_ratio
            for i, (x1, y1, x2, y2, area, conf, name) in enumerate(raw):
                if not keep[i]:
                    continue
                width = x2 - x1
                height = y2 - y1
                if (
                    name == "text"
                    and width >= min_width
                    and height <= settings["wide_noise_max_height"]
                    and conf <= settings["wide_noise_max_conf"]
                ):
                    print(
                        f"[noise] drop wide low-conf box for {_product}: "
                        f"i={i} conf={conf:.2f} box=({x1},{y1},{x2},{y2})"
                    )
                    keep[i] = False

        filtered = [raw[k] for k in range(len(raw)) if keep[k]]
        filtered = self._merge_adjacent_boxes(filtered)

        copy_frame = roi_for_yolo.copy()
        for x1, y1, x2, y2, area, conf, name in filtered:
            cv2.rectangle(copy_frame, (x1, y1), (x2, y2), (0, 0, 255), 1)
            label = f"{name} {conf:.2f}"
            cv2.putText(copy_frame, label, (x1, y1 - 5), cv2.FONT_ITALIC, 0.5, (0, 0, 0), 1)

        # cv2.imshow("Detected Image", copy_frame)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()

        def sort_with_x_tolerance(detections, tol=5):
            # detections: (gy1, gx1, cropped_img, name)
            dets = sorted(detections, key=lambda d: d[1])  # 1) x 오름차순

            out = []
            i = 0
            while i < len(dets):
                group = [dets[i]]
                j = i + 1

                # 2) x가 tol 이내로 "연속"으로 가까운 것들끼리 묶기
                while j < len(dets) and abs(dets[j][1] - group[-1][1]) <= tol:
                    group.append(dets[j])
                    j += 1

                # 3) 같은 컬럼(그룹) 안에서는 y 우선 정렬
                group.sort(key=lambda d: (d[0], d[1]))  # y, 그 다음 x
                out.extend(group)
                i = j

            return out

        detections = []

        for (x1, y1, x2, y2, area, conf, name) in filtered:
            print(f"Object: {name} -> Box: [{x1}, {y1}, {x2}, {y2}] conf={conf:.2f}")
            
            gx1 = x1 + roi_x1
            gy1 = y1 + roi_y1
            gx2 = x2 + roi_x1
            gy2 = y2 + roi_y1

            cropped_img = frame[gy1:gy2, gx1:gx2]

            WHITE = [255, 255, 255]
            cropped_img = cv2.copyMakeBorder(
                cropped_img, 
                top=10, bottom=10, left=10, right=10, 
                borderType=cv2.BORDER_CONSTANT, 
                value=WHITE
            )

            # cv2.imshow("crop img", cropped_img)
            # cv2.waitKey(0)
            # cv2.destroyAllWindows()

            # detections 항목: (gy1, gx1, cropped_img, name, (gx1, gy1, gx2, gy2))
            # 정렬/cropped/name 추출은 인덱스 0~3 사용 — return_boxes=False 호출에는
            # 영향 없음. 5번째 요소는 return_boxes=True 일 때 boxes_list 로 분리.
            detections.append((gy1, gx1, cropped_img, name, (gx1, gy1, gx2, gy2)))

        # 정렬/최종 리스트 생성은 루프 밖에서 한 번만 — 기존에는 매 반복마다
        # 전체를 재정렬(O(N^2))하고 결과 리스트를 다시 만들었다 (결과 동일).
        detections_sorted = sort_with_x_tolerance(detections, tol=5)
        cropped_images_list = [item[2] for item in detections_sorted]
        detected_names = [item[3] for item in detections_sorted]
        boxes_list = [item[4] for item in detections_sorted]

        if return_boxes:
            return cropped_images_list, detected_names, boxes_list
        return cropped_images_list, detected_names

class PaddleOCRManager:

    # 클래스 레벨 OCR 인스턴스 캐시 — PaddleOCR 생성은 모델 로드를 동반해
    # 무겁다. 설정이 고정이므로 프로세스당 1회만 생성해 재사용한다.
    _ocr_instance = None

    def __init__(self):
        pass

    @classmethod
    def _get_ocr(cls):
        if cls._ocr_instance is None:
            execution_directory = os.getcwd()

            rec_model_folder_path = os.path.join(
                execution_directory, 'ppocr', 'rec', 'en_PP-OCRv5_mobile_rec_infer')
            rec_model_folder_path = os.path.normpath(
                rec_model_folder_path).replace('\\', '/')

            det_model_folder_path = os.path.join(
                execution_directory, 'ppocr', 'det', 'PP-OCRv5_server_det_infer')
            det_model_folder_path = os.path.normpath(
                det_model_folder_path).replace('\\', '/')

            cls._ocr_instance = PaddleOCR(
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
                text_detection_model_name="PP-OCRv5_server_det",
                text_detection_model_dir=det_model_folder_path,
                text_recognition_model_name="en_PP-OCRv5_mobile_rec",
                text_recognition_model_dir=rec_model_folder_path,
                lang='en',
            )
        return cls._ocr_instance

    def _split_known_pairs(self, texts):
        """OCR 이 한 토큰으로 묶어 잡은 알려진 라벨 쌍을 분리.

        현재 'L-L L-N' 만 처리 — 화면에 토글 라벨 두 개가 나란히 있어
        OCR 이 자주 한 토큰으로 잡는다. fixed_text 비교 시 multiset 매칭이
        가능하도록 두 토큰 ['L-L', 'L-N'] 으로 분리.

        다른 케이스가 늘어나면 이 함수에 추가.
        """
        out = []
        for t in texts:
            if isinstance(t, str) and t.strip() == "L-L L-N":
                out.append("L-L")
                out.append("L-N")
            else:
                out.append(t)
        return out

    def paddleocr_basic(self, image, boxes=None):
        img_path = image  # 원본 경로 보존 (로그용)

        ocr = self._get_ocr()

        ocr_results = []
        min_score = 0.3  # 필요 시 조정

        for i, img in enumerate(image):

            if img is None or img.size == 0:
                print(f"Image index {i} is empty.")
                ocr_results.append("")
                continue

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            img = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

            try:
                # predict 호출 (input 키워드 안 써도 됨)
                pred_list = ocr.predict(img)

                joined_text = ""  # 기본값

                if pred_list:
                    # v5는 결과 "객체" 리스트
                    r_obj = pred_list[0]

                    # OCR 결과 딕셔너리로 변환
                    if hasattr(r_obj, "to_dict"):
                        r = r_obj.to_dict().get("res", {})
                    elif hasattr(r_obj, "res"):
                        r = r_obj.res
                    elif isinstance(r_obj, dict):
                        r = r_obj.get("res", r_obj)
                    else:
                        r = {}

                    rec_texts  = r.get("rec_texts", []) or []
                    rec_scores = r.get("rec_scores", []) or []
                    rec_polys  = r.get("rec_polys", r.get("dt_polys", [])) or []

                    collected = []
                    for text, score in zip(rec_texts, rec_scores):
                        t = (text or "").strip()
                        if t and float(score) >= min_score:
                            collected.append(t)

                    joined_text = " ".join(collected).strip()

                ocr_results.append(joined_text)

                print(f"[{i}] {[i]} -> {joined_text}")

            except Exception as e:
                print(f"OCR Error on image {i}: {str(e)}")
                ocr_results.append("")

        if boxes is not None:
            # boxes 동봉 호출 (Setup 등): _split_known_pairs 적용 안 함 — 토큰
            # 분리로 길이가 ocr_results != boxes 가 되면 매칭 깨짐. 사용자가
            # expected_text 에 화면 그대로 ('L-L L-N' 한 토큰) 적도록.
            return list(zip(ocr_results, boxes))
        return self._split_known_pairs(ocr_results)
