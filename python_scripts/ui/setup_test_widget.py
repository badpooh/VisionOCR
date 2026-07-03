# -*- coding: utf-8 -*-
"""Setup Test 탭 — xlsx 기반 설정값 검증.

흐름은 NewTestWidget(TEST 탭) 과 동일 패턴 — ADD TC 로 xlsx 로드, 트리에서
체크된 케이스 START 로 순차 실행, 결과 테이블 + Live Log 표시.
"""

from __future__ import annotations

import os
import traceback
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QPlainTextEdit,
    QMessageBox, QGroupBox, QTreeWidget, QTreeWidgetItem,
    QFileDialog,
)
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QFont

from function.func_connection import ConnectionManager
from ui.result_controls import ResultControlsMixin


# ---------------------------------------------------------------------------
# Workers
# ---------------------------------------------------------------------------
class ApplyDefaultsWorker(QThread):
    """Modbus default 값 일괄 write 전용 worker — 터치/OCR 없음."""

    log_line = Signal(str)
    result_row = Signal(dict)
    finished_all = Signal(str)

    def __init__(self, cases: list, product: str = "A3700N", parent=None):
        super().__init__(parent)
        self.cases = cases
        self.product = product
        self._runner = None

    def stop(self):
        if self._runner is not None:
            self._runner.cancel()

    def run(self):
        try:
            from setup_test.setup_runner import SetupRunner
            self._runner = SetupRunner(
                log_callback=lambda s: self.log_line.emit(str(s)),
            )
            results = self._runner.apply_defaults(
                cases=self.cases,
                result_callback=lambda r: self.result_row.emit(r),
            )
            ok = sum(1 for r in results if r.get("overall") == "PASS")
            skip = sum(1 for r in results if r.get("overall") == "SKIP")
            err = sum(1 for r in results
                      if r.get("overall") == "ERROR")
            self.finished_all.emit(
                f"Apply Defaults 완료 — PASS {ok} / SKIP {skip} / ERROR {err}"
            )
        except Exception as e:
            traceback.print_exc()
            self.finished_all.emit(f"에러: {e}")


class SetupTestWorker(QThread):
    log_line = Signal(str)
    result_row = Signal(dict)
    finished_all = Signal(str)

    def __init__(self, cases: list, base_save_path: str, search_pattern: str,
                 product: str = "A3700N", parent=None):
        super().__init__(parent)
        self.cases = cases
        self.base_save_path = base_save_path
        self.search_pattern = search_pattern
        self.product = product
        self._runner = None
        self._stopped = False

    def stop(self):
        self._stopped = True
        if self._runner is not None:
            self._runner.cancel()

    def run(self):
        try:
            from setup_test.setup_runner import SetupRunner
            self._runner = SetupRunner(
                log_callback=lambda s: self.log_line.emit(str(s)),
            )
            results = self._runner.run(
                base_save_path=self.base_save_path,
                search_pattern=self.search_pattern,
                product=self.product,
                cases=self.cases,
                result_callback=lambda r: self.result_row.emit(r),
            )
            self._save_results(results)
            msg = "Stopped" if self._stopped else f"완료 — {len(results)} 케이스"
            self.finished_all.emit(msg)
        except Exception as e:
            traceback.print_exc()
            self.finished_all.emit(f"에러: {e}")

    def _save_results(self, results: list):
        """0.summary.csv + 케이스별 PNG 복사."""
        import csv
        import shutil

        if not results:
            return

        def _bool_label(v):
            if v is True:
                return "OK"
            if v is False:
                return "FAIL"
            return "-"

        csv_path = os.path.join(self.base_save_path, "0.summary.csv")
        try:
            with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
                w = csv.writer(f)
                w.writerow([
                    "Name", "Value",
                    "Write", "Read", "Read Val",
                    "Defaults", "OCR",
                    "Expected", "OCR Text",
                    "Note",
                ])
                for case, r in zip(self.cases, results):
                    overall = r.get("overall", "")
                    write_label = "FAIL" if overall == "ERROR" else "OK"
                    read_label = _bool_label(r.get("read_ok"))
                    defaults_label = _bool_label(r.get("verify_defaults_ok"))
                    fixed_missing = r.get("fixed_missing") or []
                    ocr_label = "FAIL" if fixed_missing else (
                        "OK" if r.get("ocr_texts") else "-"
                    )
                    note_parts = []
                    if r.get("error"):
                        note_parts.append(str(r["error"]))
                    if fixed_missing:
                        # 항목 의미: 그냥 "텍스트" = 기대했지만 OCR 에 없음 (missing),
                        # "[unexpected] 텍스트" = OCR 엔 있지만 기대 안 한 값 (extra).
                        note_parts.append("Mismatch: " + ", ".join(fixed_missing))
                    mismatches = r.get("defaults_mismatches") or []
                    if mismatches:
                        note_parts.append(
                            "Defaults: " + " | ".join(
                                f"{n}: exp={e!r} act={a!r}" for (n, e, a) in mismatches
                            )
                        )
                    w.writerow([
                        r.get("name", ""),
                        "; ".join(str(v) for v in (r.get("target_value") or [])),
                        write_label,
                        read_label,
                        r.get("actual_value", ""),
                        defaults_label,
                        ocr_label,
                        ", ".join(case.get("expected_text") or []),
                        " | ".join(r.get("ocr_texts") or []),
                        " || ".join(note_parts),
                    ])
            self.log_line.emit(f"[save] summary csv -> {csv_path}")
        except Exception as e:
            self.log_line.emit(f"[save] csv write failed: {e}")

        for r in results:
            src = r.get("image_path")
            if not src or not os.path.isfile(src):
                continue
            safe_name = r.get("name", "case").replace("/", "_").replace("\\", "_")
            idx = r.get("index", "")
            prefix = f"{idx}." if idx != "" else ""
            dst = os.path.join(
                self.base_save_path,
                f"{prefix}{safe_name}__{os.path.basename(src)}",
            )
            try:
                shutil.copy(src, dst)
            except Exception as e:
                self.log_line.emit(f"[save] copy failed for {safe_name}: {e}")


# ---------------------------------------------------------------------------
# Widget
# ---------------------------------------------------------------------------
class SetupTestWidget(ResultControlsMixin, QWidget):
    """Setup Test 탭 — xlsx 기반 설정값 검증."""

    RESULT_HEADERS = ["#", "Name", "Overall", "Fail Summary", "Note"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.conn_manager = ConnectionManager()
        self._worker: SetupTestWorker | None = None
        self._result_row = 0
        self._init_result_controls()
        self._build_ui()

    # -----------------------------------------------------------------------
    # UI
    # -----------------------------------------------------------------------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        # 1행 — 메인 버튼
        bar1 = QHBoxLayout()
        bar1.setSpacing(6)
        self.btn_start = QPushButton("START")
        self.btn_start.setProperty("cssClass", "primary")
        self.btn_start.setMinimumWidth(80)
        self.btn_start.clicked.connect(self._handle_start)

        self.btn_stop = QPushButton("STOP")
        self.btn_stop.setProperty("cssClass", "danger")
        self.btn_stop.setMinimumWidth(80)
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._handle_stop)

        self.btn_add_tc = QPushButton("ADD TC")
        self.btn_add_tc.clicked.connect(self._handle_add_tc)

        self.btn_select_all = QPushButton("Select All")
        self.btn_select_all.clicked.connect(self._handle_select_all)

        self.btn_deselect_all = QPushButton("Deselect All")
        self.btn_deselect_all.clicked.connect(self._handle_deselect_all)

        self.btn_clear_log = QPushButton("Clear Log")
        self.btn_clear_log.clicked.connect(lambda: self.log_view.clear())

        # Apply Defaults — Modbus 만으로 default 값 일괄 write (터치/OCR 없음).
        # 기본 위치는 config/defaults_<product>.xlsx, 다이얼로그로 다른 파일도 선택 가능.
        self.btn_apply_defaults = QPushButton("Apply Defaults")
        self.btn_apply_defaults.clicked.connect(self._handle_apply_defaults)

        bar1.addWidget(self.btn_start)
        bar1.addWidget(self.btn_stop)
        bar1.addWidget(self.btn_add_tc)
        bar1.addWidget(self.btn_apply_defaults)
        bar1.addStretch()
        bar1.addWidget(self.btn_select_all)
        bar1.addWidget(self.btn_deselect_all)
        bar1.addWidget(self.btn_clear_log)
        root.addLayout(bar1)

        # 메인 — 트리 + (결과 + 로그) splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        tree_group = QGroupBox("Setup Cases")
        tree_layout = QVBoxLayout(tree_group)
        tree_layout.setContentsMargins(4, 4, 4, 4)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Cases")
        self.tree.setFont(QFont("Segoe UI", 10))
        tree_layout.addWidget(self.tree)
        splitter.addWidget(tree_group)

        right = QSplitter(Qt.Orientation.Vertical)

        result_group = QGroupBox("Results")
        result_layout = QVBoxLayout(result_group)
        result_layout.setContentsMargins(4, 4, 4, 4)
        result_layout.addLayout(self._create_result_header())
        self.result_table = QTableWidget(0, len(self.RESULT_HEADERS))
        self.result_table.setHorizontalHeaderLabels(self.RESULT_HEADERS)
        self.result_table.setAlternatingRowColors(True)
        self.result_table.verticalHeader().setVisible(False)
        self.result_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.result_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        h = self.result_table.horizontalHeader()
        widths = {0: 40, 1: 200, 2: 70, 4: 140}
        for col, w in widths.items():
            h.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)
            self.result_table.setColumnWidth(col, w)
        h.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        result_layout.addWidget(self.result_table)
        right.addWidget(result_group)

        log_group = QGroupBox("Live Log")
        log_layout = QVBoxLayout(log_group)
        log_layout.setContentsMargins(4, 4, 4, 4)
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFont(QFont("Consolas", 9))
        self.log_view.setMaximumBlockCount(2000)
        log_layout.addWidget(self.log_view)
        right.addWidget(log_group)

        right.setSizes([320, 240])
        splitter.addWidget(right)
        splitter.setSizes([260, 720])
        root.addWidget(splitter, 1)

    # -----------------------------------------------------------------------
    # ADD TC
    # -----------------------------------------------------------------------
    def _handle_add_tc(self):
        from setup_test.setup_xlsx_loader import load_setup_cases

        here = os.path.dirname(os.path.abspath(__file__))
        scripts = os.path.dirname(here)
        start_dir = os.path.join(os.path.dirname(scripts), "config")
        path, _ = QFileDialog.getOpenFileName(
            self, "Load Setup Test XLSX",
            start_dir, "Excel Files (*.xlsx);;All Files (*)",
        )
        if not path:
            return
        try:
            cases = load_setup_cases(self.conn_manager.PRODUCT, xlsx_path=path)
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"xlsx 로드 실패: {e}")
            return
        self._populate_tree(path, cases)
        self.result_table.setRowCount(0)
        self._result_row = 0
        self._reset_result_summary(0)
        self._append_log(
            f"[ui] loaded {len(cases)} case(s) from {os.path.basename(path)}"
        )

    def _populate_tree(self, xlsx_path: str, cases: list):
        self.tree.clear()
        root = QTreeWidgetItem(self.tree, [os.path.basename(xlsx_path)])
        root.setFlags(root.flags()
                      | Qt.ItemFlag.ItemIsUserCheckable
                      | Qt.ItemFlag.ItemIsAutoTristate)
        root.setCheckState(0, Qt.CheckState.Checked)
        root.setFont(0, QFont("Segoe UI", 10, QFont.Weight.Bold))
        for c in cases:
            leaf = QTreeWidgetItem(root, [c["name"]])
            leaf.setFlags(leaf.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            leaf.setCheckState(0, Qt.CheckState.Checked)
            leaf.setData(0, Qt.ItemDataRole.UserRole, c)
        self.tree.expandAll()

    def _get_checked_cases(self) -> list:
        out = []
        root = self.tree.invisibleRootItem()
        for g in range(root.childCount()):
            grp = root.child(g)
            for i in range(grp.childCount()):
                leaf = grp.child(i)
                if leaf.checkState(0) == Qt.CheckState.Checked:
                    case = leaf.data(0, Qt.ItemDataRole.UserRole)
                    if case:
                        out.append(case)
        return out

    def _handle_select_all(self):
        root = self.tree.invisibleRootItem()
        for g in range(root.childCount()):
            root.child(g).setCheckState(0, Qt.CheckState.Checked)

    def _handle_deselect_all(self):
        root = self.tree.invisibleRootItem()
        for g in range(root.childCount()):
            root.child(g).setCheckState(0, Qt.CheckState.Unchecked)

    # -----------------------------------------------------------------------
    # START / STOP
    # -----------------------------------------------------------------------
    def _handle_start(self):
        if self._worker and self._worker.isRunning():
            QMessageBox.warning(self, "Running", "이미 실행 중입니다.")
            return
        if not self.conn_manager.is_connected:
            QMessageBox.warning(self, "Connect 필요",
                                "먼저 상단 Connect 버튼으로 장치에 연결하세요.")
            return
        cases = self._get_checked_cases()
        if not cases:
            QMessageBox.warning(self, "No selection",
                                "최소 한 개의 케이스를 체크하세요.")
            return

        from demo_test.demo_process import get_image_directory
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        here = os.path.dirname(os.path.abspath(__file__))
        scripts = os.path.dirname(here)
        save = os.path.join(scripts, "results", f"setup_{ts}")
        os.makedirs(save, exist_ok=True)
        search = os.path.join(get_image_directory(), "**", "*.png")

        self.result_table.setRowCount(0)
        self._result_row = 0
        self._set_last_result_dir(save)
        self._reset_result_summary(len(cases))
        self._append_log(f"[ui] save dir = {save}")
        self._append_log(f"[ui] running {len(cases)} checked case(s)")
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)

        self._worker = SetupTestWorker(cases, save, search,
                                       product=self.conn_manager.PRODUCT)
        self._worker.log_line.connect(self._append_log)
        self._worker.result_row.connect(self._on_result)
        self._worker.finished_all.connect(self._on_finished)
        self._worker.start()

    def _handle_stop(self):
        if self._worker and self._worker.isRunning():
            self._worker.stop()
            self._append_log("[ui] STOP requested")

    # -----------------------------------------------------------------------
    # Apply Defaults — Modbus 만으로 default 값 일괄 적용
    # -----------------------------------------------------------------------
    def _handle_apply_defaults(self):
        if self._worker and self._worker.isRunning():
            QMessageBox.warning(self, "Running", "이미 실행 중입니다.")
            return
        if not self.conn_manager.is_connected:
            QMessageBox.warning(
                self, "Connect 필요",
                "먼저 상단 Connect 버튼으로 장치에 연결하세요.",
            )
            return

        from setup_test.setup_xlsx_loader import load_setup_cases

        # 기본 위치: config/defaults_<product>.xlsx
        here = os.path.dirname(os.path.abspath(__file__))
        scripts = os.path.dirname(here)
        config_dir = os.path.join(os.path.dirname(scripts), "config")
        product = self.conn_manager.PRODUCT or "A7300"
        default_name = f"defaults_{product.lower()}.xlsx"
        default_path = os.path.join(config_dir, default_name)
        start_arg = default_path if os.path.isfile(default_path) else config_dir

        path, _ = QFileDialog.getOpenFileName(
            self, "Load Defaults XLSX",
            start_arg, "Excel Files (*.xlsx);;All Files (*)",
        )
        if not path:
            return

        try:
            cases = load_setup_cases(product, xlsx_path=path)
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"xlsx 로드 실패: {e}")
            return

        # addr 비어있는 행은 skip — defaults xlsx 는 init/주석 row 도 들어올 수 있음
        cases = [c for c in cases if c.get("addr") is not None]
        if not cases:
            QMessageBox.warning(
                self, "Empty",
                "유효한 케이스 없음 (addr 컬럼 비어있음).",
            )
            return

        # Apply Defaults 는 결과 테이블 안 채움 — 로그에만 표시.
        # (초기화 작업이라 케이스별 PASS/FAIL 보다 한 줄 요약이 자연스러움)
        self._append_log(
            f"[ui] 초기화 값 적용: {len(cases)} 케이스 from "
            f"{os.path.basename(path)}"
        )
        self.btn_start.setEnabled(False)
        self.btn_apply_defaults.setEnabled(False)
        self.btn_stop.setEnabled(True)

        self._worker = ApplyDefaultsWorker(cases, product=product)
        self._worker.log_line.connect(self._append_log)
        # result_row 연결 안 함 — 결과 테이블에 row 추가 안 됨
        self._worker.finished_all.connect(self._on_apply_defaults_finished)
        self._worker.start()

    @Slot(str)
    def _on_apply_defaults_finished(self, message: str):
        self.btn_start.setEnabled(True)
        self.btn_apply_defaults.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self._worker = None
        self._append_log(f"[ui] {message}")

    # -----------------------------------------------------------------------
    # Slots
    # -----------------------------------------------------------------------
    @staticmethod
    def _fail_summary(r: dict, max_items: int = 2) -> str:
        fails = []
        for m in r.get("fixed_missing") or []:
            fails.append(f"OCR: {m}")
        if r.get("read_ok") is False:
            fails.append(
                f"Read: target={r.get('target_value')!r} actual={r.get('actual_value')!r}"
            )
        if r.get("verify_defaults_ok") is False:
            for (n, e, a) in (r.get("defaults_mismatches") or []):
                fails.append(f"Defaults: {n} exp={e!r} act={a!r}")
        if not fails:
            return "-"
        if len(fails) > max_items:
            return " | ".join(fails[:max_items]) + f" (+{len(fails)-max_items} more)"
        return " | ".join(fails)

    @Slot(dict)
    def _on_result(self, r: dict):
        row = self._result_row
        self._result_row += 1
        self.result_table.insertRow(row)
        idx = r.get("index", row + 1)
        cells = [
            str(idx),
            str(r.get("name", "")),
            str(r.get("overall", "")),
            self._fail_summary(r),
            str(r.get("note") or r.get("error") or ""),
        ]
        for c, txt in enumerate(cells):
            self.result_table.setItem(row, c, QTableWidgetItem(txt))

        overall = r.get("overall", "")
        if overall == "PASS":
            self.result_table.item(row, 2).setForeground(Qt.GlobalColor.darkGreen)
        elif overall in ("FAIL", "ERROR"):
            self.result_table.item(row, 2).setForeground(Qt.GlobalColor.red)
        elif overall == "INIT":
            self.result_table.item(row, 2).setForeground(Qt.GlobalColor.darkBlue)
        elif overall == "SKIP":
            self.result_table.item(row, 2).setForeground(Qt.GlobalColor.gray)
        self._record_result_summary(overall)
        self.result_table.scrollToBottom()

    @Slot(str)
    def _append_log(self, line: str):
        self.log_view.appendPlainText(line)

    @Slot(str)
    def _on_finished(self, message: str):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self._worker = None
        self._append_log(f"[ui] {message}")
