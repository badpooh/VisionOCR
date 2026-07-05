# -*- coding: utf-8 -*-
"""테스트 시나리오 xlsx 기본 경로 헬퍼 (단일 소스).

config 폴더가 제품별 하위 폴더로 재편됨:

    config/<제품코드>/<Kind>_<모델명>.xlsx
    예: config/A2700/Setup_Test_A2700M.xlsx
        config/A3700N/Demo_Test_A3700N.xlsx

파일명의 모델명은 제품 코드와 1:1 이 아니다 (A2700 → "A2700M").
매핑이 바뀌면 이 파일의 MODEL_SUFFIX 만 수정하면 된다.
"""

from __future__ import annotations

import os

# 제품 코드 → 파일명 모델 접미사.
# A2700 의 실제 모델명은 A2700M. 미등록 제품은 제품 코드 그대로 사용.
MODEL_SUFFIX = {
    "A2700": "A2700M",
    "A3700N": "A3700N",
    "A7300": "A7300",
}

# 사용 가능한 Kind: "Setup_Test", "Demo_Test", "Clipping_Test",
#                   "Defaults", "Source_Test"


def config_root() -> str:
    """프로젝트 루트의 config 폴더 절대 경로."""
    here = os.path.dirname(os.path.abspath(__file__))   # python_scripts/config
    scripts = os.path.dirname(here)                     # python_scripts
    return os.path.join(os.path.dirname(scripts), "config")


def product_config_dir(product: str) -> str:
    """config/<제품코드> 폴더 경로."""
    return os.path.join(config_root(), (product or "").upper())


def xlsx_path(kind: str, product: str) -> str:
    """제품별 테스트 xlsx 기본 경로.

    예: xlsx_path("Setup_Test", "A2700")
        → <root>/config/A2700/Setup_Test_A2700M.xlsx
    """
    p = (product or "").upper()
    model = MODEL_SUFFIX.get(p, p)
    return os.path.join(product_config_dir(p), f"{kind}_{model}.xlsx")
