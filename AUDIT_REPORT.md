# VisionOCR 코드 진단 리포트

**감사 일자**: 2026-05-03
**범위**: `C:\Users\JOYS\Documents\Claude\Projects\vision\VisionOCR\` (단, `python_env/`는 제외)
**축**: 코드 품질 / 정리 + 구조 / 아키텍처
**전제**: 동작 100% 보존(behavior preservation). 본 리포트는 변경 권고만 제시 — 코드 수정은 별도 단계.

---

## 0. 한 줄 요약

총 라이브 Python 코드 약 6,590 LoC 중에서, 안전하게 제거 가능한 데드 코드 **약 2,000 LoC**(demo_function 1335 + demo_config 529 + func_process 36 + config_setting 163 + .bak 5개) 와, 단일 소스화가 필요한 **3쌍의 중복 정의** (`_NATIVE_MODBUS_PRODUCTS`, `SUPPORTED_PRODUCTS`, `config_map/roi`)가 핵심입니다. 그 다음으로 `func_modbus.py`의 탭 인덴테이션 + 80줄 주석 데드블록, OCR 모델 lifecycle, 잠재 NameError가 손댈 가치가 있습니다.

---

## 1. High Priority

### H1. `func_process.py:30` — 항상 True 가 되는 조건문 (논리 버그)

```python
if test_mode == "Demo" or "NoLoad":   # ← "NoLoad"는 항상 truthy
```

올바른 의도: `if test_mode in ("Demo", "NoLoad"):`. **다만 `func_process.py` 모듈 자체가 어디서도 import되지 않음(=데드)** 이라 현재 동작에는 영향 없음. 모듈 삭제(H3)와 함께 처리.

### H2. `demo_test/demo_function.py` (1,335 LoC) — 100% 미사용 데드코드

- `grep "from demo_test.demo_function|import demo_function"` → 매치 0건. 자기 자신 외에는 어디서도 참조하지 않음.
- 파일 안에 별개의 `ModbusManager` (`func_connection.ConnectionManager`와 충돌 모양) + 별개의 `TouchManager` (`func_touch.TouchManager`와 충돌)이 존재. 모듈 레벨에 하드코드 IP `SERVER_IP = '10.10.26.159'`.
- 명백한 미정의 속성 참조: `self.coords_TA["touch_mode"]` (line 142~192, 18군데). `__init__`에서 `coords_TA` 정의 없음 → 호출 시 `AttributeError`.
- 듀얼 import: `import time` (4, 8), `import threading` (3, 10).

**권고**: 파일 통째 삭제. 위험도 낮음 (사용처 없음).

### H3. `demo_test/demo_config.py` (529 LoC) — H2 외엔 사용처 없음

`from demo_test.demo_config import ...` 매치는 demo_function.py 6줄뿐 → demo_function 삭제 시 동반 데드. 같이 삭제.

### H4. `function/func_process.py` (36 LoC) — 미사용

`grep func_process|TestProcess` → 자기 파일만 매치. `MainWindow._handle_start`은 `TestRunnerWorker`를 직접 호출하고 `TestProcess`는 거치지 않음. 삭제.

### H5. `config/config_setting.py` (163 LoC) — 미사용

`grep config_setting|SettingList` → 자기 파일만 매치. `DEFAULT_CHECKBOX_STATES`, `CHECKBOX_MAPPING`, `DASHBORAD_TEST` 모두 어느 위젯에서도 안 씀. CHECKBOX_MAPPING과 DASHBORAD_TEST는 60+ 라인이 주석 처리. 삭제.

### H6. `_NATIVE_MODBUS_PRODUCTS` 4곳 중복 + 의미 불일치 (잠재 라우팅 버그)

| 위치 | 값 | 비고 |
|---|---|---|
| `func_connection.py:51` | `("A7300",)` | tuple |
| `func_modbus.py:67` | `frozenset({"A7300", "A3700N"})` | **다른 3곳과 다름** |
| `func_touch.py:18` | `{"A7300"}` | set |
| `demo_process.py:21` | `("A7300",)` | tuple |

`func_modbus.ModbusLabels.uses_native_modbus_ui()`의 docstring은 *"펌웨어가 Modbus UI 테스트 모드 … A7300 만 True"* 라고 하지만, 실제 `NATIVE_MODBUS_PRODUCTS`는 A3700N도 포함. 그 결과:

- `test_mode_off()` (line 121): `uses_native_modbus_ui()`로 가드한 뒤 `ConfigMapA7300` 주소들에 직접 write → A3700N 연결 시 잘못된 주소 write 가능.
- `read_float()` (line 156): aggregation_selection write를 A3700N에서도 실행 — 코멘트(155~158)는 "A3700N에 안 좋음, 스킵해야 함"이라 적었으면서 실제 가드는 안 막음.

**권고**: `models/config.py`에 단일 정의 후 4곳 모두 import. 의미 불일치는 별도 결정 필요(아래 D1 참조).

### H7. `SUPPORTED_PRODUCTS` 이중 정의

- `models/config.py:11` — `(PRODUCT_A7300, PRODUCT_A3700N, PRODUCT_A2700)` (단일 소스 의도)
- `func_connection.py:10` — `("A7300", "A3700N", "A2700")` + 코멘트 *"models/config.py의 SUPPORTED_PRODUCTS와 동기화"*

**권고**: `func_connection.ConnectionManager.SUPPORTED_PRODUCTS`를 `models.config.SUPPORTED_PRODUCTS`로 교체.

### H8. `config_map.py` ≡ `config_map_a7300.py`, `config_roi.py` ≡ `config_roi_a7300.py` (헤더만 다름)

```
$ diff config_map.py config_map_a7300.py
0a1,6
> # 헤더 코멘트만 다름
```

전이기간 산물로 보임. 라이브 import 위치:
- `func_evaluation.py:15-16` — `config_roi`, `config_map` (제품 무관, A7300 가정)
- `demo_process.py:7-10` — `config_touch`, `config_demo_roi`, `config_map`
- `setup_process.py:30-31`, `setup_config.py:30-31` — `config_map`, `config_touch`
- `func_touch.py:6` — `config_touch`

**권고**: `config_map.py` / `config_roi.py` 를 삭제 — 사용처가 모두 A7300 기준이고, 진짜 제품-aware 코드는 이미 `config.config_product.get_map_module()` / `get_roi_module()`을 통해 `_a7300/_a3700n` 버전을 로드함. 두 파일 삭제 + 위 import들을 `_a7300` 버전으로 변경하면 deprecated 듀얼 카피 제거. 위험: `config_roi.py`(663 LoC)와 `config_map.py`(483 LoC)가 정말 byte-equal인지 데이터까지 한 번 더 검증 후 진행.

### H9. `.bak` 파일 5개 — git이 있으니 history로 충분

```
config/config_map_a3700n.py.bak.1777721755
config/config_map_a3700n.py.bak.1777724433
function/func_modbus.py.bak.1777721816
function/func_modbus.py.bak.1777724460
ui/main_window.py.bak.1777381230
```

**권고**: 삭제. git log + git show로 동일 정보 접근 가능.

### H10. 탭 인덴트 (5개 파일) + `func_modbus.py` 데드 블록 85줄

- **탭 인덴트 사용 라이브 파일** (다른 모든 모듈은 4-space):
  - `function/func_modbus.py`
  - `demo_test/demo_process.py`
  - `config/config_setting.py` (단, H5에 의해 삭제 후보)
  - `config/config_test_mode_value.py`
  - `config/config_touch.py`
- PEP 8 위반 + 탭/스페이스 혼합 모듈 import 시 IndentationError 위험.
- `func_modbus.py:336~337`: `if False:  # 아래 if-블록 단순 무력화` (데드 가드).
- `func_modbus.py:453~540`: setup_initialization 옛 본문 **85줄** 주석 처리 (검증됨).

**권고**: 4개 라이브 파일 (config_setting 제외) 인덴트를 4-space로 변환 + 주석 데드블록 삭제. 자동 변환 도구(autopep8 / Python `tabnanny`) 후 diff 검증 권장.

---

## 2. Medium Priority

### M1. `func_ocr.YoloManager.yolo_basic` 모델 이중 로드

```python
# __init__:
self.model = YOLO(self.MODEL_PATH)
# yolo_basic line 40:
model = YOLO(self.MODEL_PATH)   # 매 호출마다 다시 로드
```

`self.model` 사용으로 변경. 매 호출 시 디스크 I/O 절약.

### M2. `PaddleOCRManager.paddleocr_basic` 매 호출마다 OCR 인스턴스 생성

`paddleocr_basic` 함수 안에서 `ocr = PaddleOCR(...)` 인스턴스화. PaddleOCR 객체는 무거움. `__init__` 또는 lazy property로 한 번만.

추가로 `demo_process.py:39`, `setup_process.py:36`에서 모듈 레벨 `paddleocr_func = PaddleOCRManager()` — 두 모듈이 둘 다 import되면 두 번 로드 (현재 `__init__`이 `pass`라 가벼우나, M2 적용하면 무거워짐).

### M3. `func_ocr.yolo_basic` 잠재 NameError

```python
for (x1, y1, ...) in filtered:
    ...
    cropped_images_list = [item[2] for item in detections_sorted]
    detected_names = [item[3] for item in detections_sorted]

return cropped_images_list, detected_names
```

`filtered`가 빈 리스트면 두 변수가 정의되지 않은 채 return → `UnboundLocalError`. 함수 시작에서 `cropped_images_list = []; detected_names = []` 초기화.

### M4. `func_evaluation.eval_test_mode_balance` 4지선다 브랜치 중복

라인 395~430의 `if ratio and timestamp / ratio only / timestamp only / neither` 4 브랜치는 거의 동일한 호출 시퀀스. 가드 절(`if ratio: ...; if timestamp: ...`)로 단순화 가능. 동작 미세 변경 가능성 있어 100% 보존 모드면 보류.

### M5. `func_touch.input_number` 12자리 if/elif 두 번

라인 288~342에서 digit '0'~'9', '.', '-' 12분기를 두 번 (default key + ref key). dict로 매핑:

```python
NUM_KEYS = {'0': ConfigTouch.touch_btn_number_0, ...}
NUM_KEYS_REF = {'0': ConfigTouch.touch_btn_ref_num_0, ...}
def input_number(self, number_str, key_type=None):
    table = NUM_KEYS_REF if key_type == 'ref' else NUM_KEYS
    for digit in number_str:
        member = table.get(digit)
        if member: self.touch_menu(member.value)
        else: print("input number touch error")
```

48줄 → 약 10줄.

### M6. `func_ocr.py:9-11` PaddlePaddle monkey-patch

```python
import paddle.base.libpaddle as _libpaddle
if not hasattr(_libpaddle.AnalysisConfig, 'set_optimization_level'):
    _libpaddle.AnalysisConfig.set_optimization_level = lambda self, level: None
```

런타임 모듈 패치 — paddleocr/paddlepaddle 버전 호환 hack으로 추정. `# 어느 버전 / 왜 / 언제까지` 코멘트 권장.

### M7. `device.io_a7300.A7300DeviceIO.screenshot()`은 항상 raises

```python
def screenshot(self) -> bytes:
    ...
    raise DeviceIOError("A7300 native screenshot returns no bytes through this API; ...")
```

`DeviceIO.screenshot() -> bytes` 인터페이스 계약을 위반. 호출자가 폴리모픽으로 쓰면 깨짐. 다행히 현재 `func_touch.screenshot()`은 `self._uses_bridge()`로 분기해서 A7300은 이쪽 경로를 안 탐 — 동작은 OK이지만 **`DeviceIO` 추상화의 약속이 사실상 거짓**. 인터페이스 시그니처를 `Optional[bytes]` 반환으로 바꾸거나, A7300은 별도 인터페이스 사용.

### M8. demo_process / setup_process 모듈 레벨 사이드이펙트

```python
# demo_process.py:39, setup_process.py:36
paddleocr_func = PaddleOCRManager()
yolo_func = YoloManager()
```

`from demo_test.demo_process import ...`만 해도 YOLO 모델 디스크 로드. `MainWindow.__init__`에서 단순 import만 해도 무거워짐. lazy 또는 클래스 멤버로 옮기기.

### M9. `__init__.py` 누락

| 모듈 | `__init__.py` |
|---|---|
| `demo_test/` | **없음** |
| `config/` | **없음** |
| `function/` | **없음** |
| `setup_test/` | 0 bytes |
| `ui/` | 0 bytes |
| `models/` | 0 bytes |
| `device/` | 344 bytes (re-export) |

implicit namespace package(PEP 420)로 동작하긴 함. 빈 `__init__.py` 추가가 안전 (PyInstaller, 일부 IDE에서 더 잘 인식).

### M10. `models/database.py:21` 무조건 print

```python
def initialize_database():
    with _connect() as conn:
        ...
    print("Database and table have been initialized.")
```

앱 부트 시마다 stdout 출력. logging 사용 또는 silent.

### M11. `models/database.py:33` `str | None` 타입 힌트

`PEP 604` 신택스 → Python 3.10+. 임베디드 `python_env`가 3.10 미만이면 `SyntaxError`. 환경 확인 필요.

---

## 3. Low Priority (위생)

### L1. 의미 없는 alias / 미사용 import

- `func_evaluation.py:16` — `from config.config_map import ConfigMap as ConfigMap` (alias 의미 없음).
- `func_ocr.py:13` — `from config.config_demo_roi import Configs` (`Configs` 사용처 없음).
- `func_evaluation.py:9` — `import time` — `time` 사용 한 군데(`time.sleep(delay)` line 69) 있어 OK.

### L2. `.gitignore` 누락 항목

현재:
```
*.pyc
build/
dist/
__pycache__/
```

권고 추가: `python_env/`, `.vscode/`, `settings.db`, `results/`, `bridge_screenshots/`, `*.bak.*`, `.gradle/`, `installer_output/`, `__pycache__` (이미 있지만 디스크에 9개 디렉토리 잔존 — 이미 트래킹된 거면 `git rm -r --cached`).

### L3. `.gradle/` 디렉토리 잔존 — 자바 흔적

`main.py` 코멘트에 *"JavaFX AppView.fxml + AppController 를 대체"*. 과거 자바 프로젝트 흔적. `.gradle/` 폴더 자체가 미사용이면 삭제.

### L4. `demo_process.py:62` 주석 처리된 print

```python
# print(f"SetupProcess: AccuraSM checked={state}")
```

살릴지 지울지 결정.

### L5. `config_map_a3700n.py.bak.*` 2개 + `func_modbus.py.bak.*` 2개

H9에 포함.

### L6. `config_test_mode_value.py` (176 LoC) — 살아있음

`demo_process.py`에서 `from config.config_test_mode_value import TestModeBalance as tmb`로 사용. 정상.

---

## 4. 구조 / 아키텍처 노트 (변경 권고 아님)

### A1. 듀얼 entrypoint는 의도된 패턴

- `main.py` (root) — IDE/VSCode용 sys.path 어댑터 런처 (33 LoC, 코멘트 양호).
- `python_scripts/main.py` — 실제 본체.
- `run.bat` → `python_scripts/main.py` 호출 (production).
- `installer.iss` → `run.bat`로 wrap. 

문제 없음. 그대로 유지.

### A2. 제품-aware 디스패치는 두 갈래로 굴러감

- **Modbus 측**: `function.func_modbus.ModbusLabels` + `function.func_touch.TouchManager`가 `connect_manager.PRODUCT`를 직접 보고 if-분기.
- **DeviceIO 측**: `device.loader.get_device_io(product)` → `A7300DeviceIO` / `A3700NDeviceIO` / `A2700DeviceIO` 다형성.

`func_touch.TouchManager.touch_menu()` 안에서 _uses_bridge() 분기 → 브릿지 케이스에선 `device.get_device_io()`로 위임. 즉 두 패턴이 공존 + 위임 다리가 한 군데. 일관성을 추구한다면 `TouchManager` 자체를 product별로 split 하거나, `ModbusLabels`도 `DeviceIO` 인터페이스로 흡수하는 길이 있지만, **이는 동작 보존 모드 밖으로 나가는 큰 변경**. 권고 X (참고만).

### A3. `device.io_a2700.A2700DeviceIO`가 `A3700NDeviceIO` 상속

```python
class A2700DeviceIO(A3700NDeviceIO):
    product = "A2700"
```

A2700 ≅ A3700N(브릿지 동일 프로토콜) 가정. 코멘트에 명기됨. OK.

### A4. `device.io_a7300.A7300DeviceIO.__init__` 지연 import

```python
from function.func_touch import TouchManager
from config.config_touch import ConfigTouch
```

순환 의존 회피 코멘트 명기. OK.

---

## 5. 디스크 위생

| 항목 | 상태 | 권고 |
|---|---|---|
| `__pycache__/` 9개 디렉토리 | 디스크에 잔존 | `find . -name __pycache__ -type d -prune -exec rm -rf {} \;` (gitignore 적용 후) |
| `.bak.*` 5개 | git 사용 중이면 불필요 | 삭제 |
| `.gradle/` | 자바 시절 흔적 | 미사용이면 삭제 |
| `python_env/` | gitignore에 미포함 | gitignore 추가 |
| `settings.db` | 사용자 데이터, 트래킹 비추 | gitignore 권고 |
| `results/`, `bridge_screenshots/` | 런타임 산출물 | gitignore 권고 |

---

## 6. 결정 필요 항목 (Decision points)

### D1. `_NATIVE_MODBUS_PRODUCTS` 의미 통일

현재 함수 이름은 `uses_native_modbus_ui()` 하나지만 의미가 두 갈래임:

- (a) "Modbus UI 테스트 모드(가상 터치/캡처) 지원" — A7300만.
- (b) "setup_client(502)을 통한 측정값 read 가능" — A7300, A3700N(브릿지로 setup_client 연결됨).

두 의미를 하나의 set으로 묶을 수 없음. 함수와 set을 둘로 쪼개야 정확:
- `MODBUS_TEST_MODE_PRODUCTS = {"A7300"}` → `supports_modbus_ui_testmode()`
- `SETUP_CLIENT_PRODUCTS = {"A7300", "A3700N"}` → `has_setup_client()`

**결정 필요**: 현재 `func_modbus.py:79`의 `frozenset({"A7300", "A3700N"})`이 의도적인지 (의미 b를 노린 건지), 아니면 docstring대로 a를 의도했는데 잘못 적은 건지. 이건 코드만 봐서는 결론 못 냄 — **사용자/도메인 지식 필요**.

### D2. `config_map.py` / `config_roi.py` 삭제 vs shim

- 삭제: import한 4~5 군데를 `_a7300` 버전으로 변경. 가장 깨끗.
- shim: `from .config_map_a7300 import *` 한 줄로 재노출. 호환성 안전.

선호 결정 필요. 동작 보존 100%를 더 중시하면 shim, 코드베이스 정리를 더 중시하면 삭제.

### D3. Step 1(데드코드 삭제)을 한 번에 묶을지 별도 PR로 쪼갤지

권장: 단일 PR로 묶음. 이유: 모두 무사용 파일 삭제 → 충돌 가능성 없음, diff가 (-) 만으로 깔끔.

---

## 7. 권고 작업 순서 (위험도 순)

| Step | 내용 | 추정 노력 | 위험 | 동작 변경 |
|---|---|---|---|---|
| 1 | 데드 파일 삭제: H2, H3, H4, H5, H9 | S | 낮음 | 없음 |
| 2 | 단일 소스화: H7 (SUPPORTED_PRODUCTS), H8 (config_map/roi) | S | 낮음 | 없음 |
| 3 | `func_modbus.py` / `demo_process.py` 인덴테이션 통일 + 데드블록 정리 (H10) | M | 중 (자동 변환 후 diff 검증 필수) | 없음 (검증되면) |
| 4 | `_NATIVE_MODBUS_PRODUCTS` 단일 소스화 (H6) | S | **D1 결정 필요** | 잠재 — A3700N 라우팅 |
| 5 | M1, M3 (yolo 모델 이중 로드, NameError 방지) | S | 낮음 | 없음 |
| 6 | M2, M8 (PaddleOCR/Yolo lifecycle) | M | 중 | 없음 (메모리/성능 개선) |
| 7 | M4, M5 (eval 4브랜치, input_number) | M | 중 | 미세 동작 변경 가능 — 100% 보존 모드면 보류 |
| 8 | L 항목들 (위생) | S | 낮음 | 없음 |

---

## 8. 본 리포트의 한계 / 추가 확인 권고

- **테스트 부재**: 프로젝트에 자동 테스트가 없어 보임. 위 권고 적용 시 회귀를 잡으려면 최소한 "앱 시작 → connect → 한 테스트케이스 실행" 스모크 시나리오를 수동으로 정해두는 게 좋음.
- **임베디드 `python_env` 버전 미확인**: M11(`str | None`)은 3.10 미만이면 폭발. 빌드용 파이썬 버전 확인 필요.
- **`config_map.py` ↔ `config_map_a7300.py` byte-equality**: 헤더 외에는 동일하다고 `diff`가 보였으나, 663 LoC와 489 LoC 등 길이 차이가 있음 — **재검증 권장** (혹은 `config_roi.py` 663 vs `config_roi_a7300.py` 669 → 6줄 차이는 무엇?).

---

## 9. 다음 단계

이 리포트를 바탕으로 어디까지 손댈지 다시 결정하면, surgical change PR 단위로 쪼개서 진행 가능합니다. 추천 시작점은 **Step 1 (데드 파일 삭제)** — 위험 0, 효과(-2,000 LoC) 즉시.
