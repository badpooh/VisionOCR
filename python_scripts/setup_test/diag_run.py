"""
Setup Test 단일 항목 진단 러너 (standalone, GUI 없이).

사용:
    cd python_scripts
    ..\python_env\python.exe -m setup_test.diag_run --item Wiring --values 0,1
    ..\python_env\python.exe -m setup_test.diag_run --list
    ..\python_env\python.exe -m setup_test.diag_run --item Wiring --skip-write

vision 앱이 떠 있지 않아도 동작. ConnectionManager에 직접 IP/포트/제품을 주입해서
브릿지 + Modbus 연결을 만든 뒤 한 항목만 끝까지 돌려봄. 결과 PNG/CSV는
python_scripts/results/setup_diag_<timestamp>/ 에 저장.
"""

from __future__ import annotations

import argparse
import os
import sys
import traceback
from datetime import datetime


def _setup_pythonpath():
    """python_scripts/ 를 sys.path 에 (어디서 실행해도 동작하도록)."""
    here = os.path.dirname(os.path.abspath(__file__))
    parent = os.path.dirname(here)
    if parent not in sys.path:
        sys.path.insert(0, parent)


_setup_pythonpath()


def list_items():
    from setup_test.setup_config import SETUP_GROUPS
    print("=== SETUP_GROUPS ===")
    for g, cats in SETUP_GROUPS.items():
        print(f"  [{g}]")
        for c, items in cats.items():
            for it in items:
                vals = it.get("values", [])
                addr = it.get("addr")
                addr_name = getattr(addr, "name", "?") if addr else "?"
                print(f"    - {it['name']:<35} addr={addr_name:<35} type={it.get('type','?'):<7} values={vals}")


def find_item(name):
    from setup_test.setup_config import SETUP_GROUPS
    for cats in SETUP_GROUPS.values():
        for items in cats.values():
            for it in items:
                if it["name"].lower() == name.lower():
                    return it
    return None


def main():
    parser = argparse.ArgumentParser(description="Setup Test 단일 항목 진단 러너")
    parser.add_argument("--list", action="store_true", help="setup_config 항목 나열 후 종료")

    parser.add_argument("--ip", default="192.168.0.10", help="장치 IP (Modbus). 기본 192.168.0.10")
    parser.add_argument("--setup-port", type=int, default=502, help="Modbus 502")
    parser.add_argument("--touch-port", type=int, default=5100, help="A7300 가상 터치 (A3700N은 무시됨)")
    parser.add_argument("--product", default="A3700N", choices=("A7300", "A3700N", "A2700"))

    parser.add_argument("--item", help="실행할 항목 이름 (--list로 확인)")
    parser.add_argument("--values", help="콤마 분리 정수 목록 (예: 0,1). 생략 시 setup_config의 values 사용")

    parser.add_argument("--skip-write", action="store_true", help="Modbus write/read 스킵 (UI+OCR만)")
    parser.add_argument("--skip-touch", action="store_true", help="UI 터치 스킵 (write/read만)")
    parser.add_argument("--no-preflight", action="store_true", help="preflight 스킵")

    args = parser.parse_args()

    if args.list:
        list_items()
        return 0

    if not args.item:
        parser.error("--item 또는 --list 가 필요합니다")

    item = find_item(args.item)
    if item is None:
        print(f"[ERR] '{args.item}' 항목을 찾을 수 없음. --list 로 확인.")
        return 2

    if args.values:
        try:
            override_values = [int(v.strip()) for v in args.values.split(",") if v.strip()]
        except ValueError:
            print(f"[ERR] --values 파싱 실패: {args.values}")
            return 2
        # 원본 dict는 건드리지 않고 복사본에 적용
        item = dict(item)
        item["values"] = override_values

    # ConnectionManager 설정 + 연결
    from function.func_connection import ConnectionManager
    cm = ConnectionManager()
    cm.set_product(args.product)
    cm.ip_connect(args.ip)
    cm.tp_update(args.touch_port)
    cm.sp_update(args.setup_port)
    cm.tcp_connect()
    print(f"[diag] connected={cm.is_connected} product={cm.PRODUCT} "
          f"ip={cm.SERVER_IP} setup={cm.SETUP_PORT} touch={cm.TOUCH_PORT}")

    # 결과 폴더
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    here = os.path.dirname(os.path.abspath(__file__))
    save_dir = os.path.abspath(os.path.join(here, "..", "results", f"setup_diag_{ts}"))
    os.makedirs(save_dir, exist_ok=True)
    print(f"[diag] save_dir = {save_dir}")

    # Runner
    from setup_test.setup_process import SetupTestRunner
    runner = SetupTestRunner(base_save_path=save_dir)

    if not args.no_preflight:
        ok = runner.preflight()
        print(f"[diag] preflight overall = {ok}")

    # 모드 분기
    if args.skip_write and args.skip_touch:
        print("[diag] --skip-write 와 --skip-touch 동시 지정 → 할 일이 없음")
        return 1

    try:
        if args.skip_touch:
            # write/read만
            for v in item.get("values", []):
                runner._unlock_setup()
                w = runner._write_value(item, v)
                rv = runner._read_value(item) if w else None
                print(f"[diag-write-only] {item['name']}={v}  write={w}  read={rv}  match={rv == v}")
        elif args.skip_write:
            # touch + ocr만 (디바이스 자체 상태값 확인)
            for v in item.get("values", []):
                runner.touch_manager.uitest_mode_start()
                runner._navigate_and_input(item, v)
                ocr_ok, expected, ocr_text, saved = runner._verify_ocr(item, v)
                print(f"[diag-touch-only] {item['name']}={v}  ocr_ok={ocr_ok} "
                      f"expected={expected!r} text={ocr_text!r} png={saved}")
        else:
            results = runner.run_single_item(item)
            print(f"\n=== 요약 ===")
            for r in results:
                print(f"  {r['name']}={r['value']}  write={r['write']} "
                      f"read={r['read_value']} ocr_ok={r['ocr_ok']} "
                      f"expected={r['ocr_expected']!r}  → {r['note']}")
    except Exception as e:
        traceback.print_exc()
        print(f"[diag] 예외: {e}")
        return 3
    finally:
        try:
            cm.tcp_disconnect()
        except Exception:
            pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
