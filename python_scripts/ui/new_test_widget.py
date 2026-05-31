# -*- coding: utf-8 -*-
"""New Test 탭 — A3700N 데모 모드 + 외부소스 옵션.

Setup Test 의 트리 + 결과 테이블 + 로그 레이아웃을 모방.
- ADD TC: xlsx 파일 다이얼로그 → 트리에 케이스들을 새로 채움 (덮어쓰기).
- Select All / Deselect All / Clear Log: Setup Test 와 동일.
- START: 트리에서 체크된 케이스만 순차 실행.
- Use External Source (CMC256) 체크박스 + Setup 버튼 — 외부소스 인가 옵션.

전제: 상단 Connect 버튼으로 ConnectionManager 가 이미 연결돼 있어야 함.
실행 시 PRODUCT 는 자동으로 A3700N 으로 강제.
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
    QCheckBox, QDialog, QFormLayout, QLineEdit, QDialogButtonBox,
    QFileDialog,
)
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QFont

from function.func_connection import ConnectionManager
from models import config as app_config


# ---------------------------------------------------------------------------
# Worker
# ---------------------------------------------------------------------------
class NewTestWorker(QThread):
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
            from demo_test.demo_a3700n_runner import DemoModeA3700NRunner
            self._runner = DemoModeA3700NRunner(
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
        """summary.csv + 케이스별 PNG 복사."""
        import csv
        import shutil

        if not results:
            return

        csv_path = os.path.join(self.base_save_path, "0.summary.csv")
        try:
            with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
                w = csv.writer(f)
                w.writerow([
                    "#", "name", "overall",
                    "fixed_missing", "meas_pass_count",
                    "ocr_texts", "meas_results",
                    "ratio_results", "timestamp_results",
                    "fixed_text_expected",
                    "meas_low", "meas_high", "meas_unit",
                    "ratio_low", "ratio_high", "ratio_text", "ratio_unit",
                    "reset", "timestamp_count", "timestamp_margin_sec",
                    "reset_time",
                    "error", "image_path",
                ])
                for case, r in zip(self.cases, results):
                    reset_time = case.get("_reset_time")
                    w.writerow([
                        r.get("index", ""),
                        r.get("name", ""),
                        r.get("overall", ""),
                        ", ".join(r.get("fixed_missing") or []),
                        r.get("meas_pass_count", ""),
                        " | ".join(r.get("ocr_texts") or []),
                        " | ".join(r.get("meas_results") or []),
                        " | ".join(r.get("ratio_results") or []),
                        " | ".join(r.get("timestamp_results") or []),
                        ", ".join(case.get("fixed_text") or []),
                        ";".join(str(v) for v in (case.get("meas_low") or [])),
                        ";".join(str(v) for v in (case.get("meas_high") or [])),
                        case.get("meas_unit") or "",
                        ";".join(str(v) for v in (case.get("ratio_low") or [])),
                        ";".join(str(v) for v in (case.get("ratio_high") or [])),
                        ", ".join(case.get("ratio_text") or []),
                        case.get("ratio_unit") or "",
                        "TRUE" if case.get("reset") else "",
                        case.get("timestamp_count") if case.get("timestamp_count") is not None else "",
                        case.get("timestamp_margin_sec") if case.get("timestamp_margin_sec") is not None else "",
                        reset_time.strftime("%Y-%m-%d %H:%M:%S") if reset_time else "",
                        r.get("error", ""),
                        r.get("image_path", ""),
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
# CMC256 Setup 다이얼로그 (PoC, placeholder)
# ---------------------------------------------------------------------------
class CMC256SetupDialog(QDialog):
    """Omicron CMC256 외부소스 설정 — 통신은 추후 구현."""

    def __init__(self, parent=None, current: dict = None):
        super().__init__(parent)
        self.setWindowTitle("CMC256 Setup")
        self.resize(360, 220)
        cur = current or {}

        layout = QFormLayout(self)
        self.fld_ip = QLineEdit(cur.get("ip", "192.168.0.100"))
        self.fld_port = QLineEdit(cur.get("port", "4711"))
        self.fld_voltage = QLineEdit(cur.get("voltage", "220"))
        self.fld_current = QLineEdit(cur.get("current", "5"))
        self.fld_freq = QLineEdit(cur.get("freq", "60"))

        layout.addRow("IP:", self.fld_ip)
        layout.addRow("Port:", self.fld_port)
        layout.addRow("Voltage (V):", self.fld_voltage)
        layout.addRow("Current (A):", self.fld_current)
        layout.addRow("Frequency (Hz):", self.fld_freq)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addRow(btns)

    def values(self) -> dict:
        return {
            "ip": self.fld_ip.text(),
            "port": self.fld_port.text(),
            "voltage": self.fld_voltage.text(),
            "current": self.fld_current.text(),
            "freq": self.fld_freq.text(),
        }


# ---------------------------------------------------------------------------
# Widget
# ---------------------------------------------------------------------------
class NewTestWidget(QWidget):
    """A3700N 데모 모드 + 외부소스 옵션 PoC 탭."""

    RESULT_HEADERS = ["#", "Name", "Overall", "Fail Summary", "Note"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.conn_manager = ConnectionManager()
        self._worker: NewTestWorker | None = None
        self._result_row = 0
        self._cmc256_settings: dict = {}
        self.cb_external = QCheckBox()
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

        bar1.addWidget(self.btn_start)
        bar1.addWidget(self.btn_stop)
        bar1.addWidget(self.btn_add_tc)
        bar1.addStretch()
        bar1.addWidget(self.btn_select_all)
        bar1.addWidget(self.btn_deselect_all)
        bar1.addWidget(self.btn_clear_log)
        root.addLayout(bar1)

        # 메인 — 트리 + (결과 + 로그) splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 왼쪽 트리
        tree_group = QGroupBox("Test Cases")
        tree_layout = QVBoxLayout(tree_group)
        tree_layout.setContentsMargins(4, 4, 4, 4)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Cases")
        self.tree.setFont(QFont("Segoe UI", 10))
        tree_layout.addWidget(self.tree)
        splitter.addWidget(tree_group)

        # 오른쪽 (결과 + 로그)
        right = QSplitter(Qt.Orientation.Vertical)

        result_group = QGroupBox("Results")
        result_layout = QVBoxLayout(result_group)
        result_layout.setContentsMargins(4, 4, 4, 4)
        self.result_table = QTableWidget(0, len(self.RESULT_HEADERS))
        self.result_table.setHorizontalHeaderLabels(self.RESULT_HEADERS)
        self.result_table.setAlternatingRowColors(True)
        self.result_table.verticalHeader().setVisible(False)
        self.result_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.result_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        h = self.result_table.horizontalHeader()
        # 0:#  1:Name  2:Overall  3:Fail Summary  4:Note
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
    # ADD TC = xlsx 로드 → 트리 새로 채움
    # -----------------------------------------------------------------------
    def _handle_add_tc(self):
        from demo_test.demo_xlsx_loader import load_demo_cases

        here = os.path.dirname(os.path.abspath(__file__))
        scripts = os.path.dirname(here)
        start_dir = os.path.join(os.path.dirname(scripts), "config")
        path, _ = QFileDialog.getOpenFileName(
            self, "Load Test Case XLSX",
            start_dir, "Excel Files (*.xlsx);;All Files (*)",
        )
        if not path:
            return
        try:
            cases = load_demo_cases(self.conn_manager.PRODUCT, xlsx_path=path)
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"xlsx 로드 실패: {e}")
            return
        self._populate_tree(path, cases)
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
    # 외부 소스 Setup
    # -----------------------------------------------------------------------
    def _handle_setup_source(self):
        dlg = CMC256SetupDialog(self, current=self._cmc256_settings)
        if dlg.exec():
            self._cmc256_settings = dlg.values()
            self._append_log(f"[ui] CMC256 settings: {self._cmc256_settings}")

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

        # PRODUCT 가 데모 모드 지원 제품인지 검증 (A7300/A3700N/A2700)
        if self.conn_manager.PRODUCT not in app_config.DEMO_TEST_MODE_PRODUCTS:
            QMessageBox.warning(
                self, "Unsupported product",
                f"현재 PRODUCT={self.conn_manager.PRODUCT} 는 데모 테스트를 지원하지 않습니다.\n"
                f"지원: {', '.join(app_config.DEMO_TEST_MODE_PRODUCTS)}",
            )
            return

        if self.cb_external.isChecked():
            self._append_log(
                f"[ui] External source ON (CMC256). settings={self._cmc256_settings}"
            )
            self._append_log(
                "[ui] (외부 소스 인가는 추후 구현 — 현재는 로그만)"
            )

        from demo_test.demo_process import get_image_directory
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        here = os.path.dirname(os.path.abspath(__file__))
        scripts = os.path.dirname(here)
        save = os.path.join(scripts, "results", f"newtest_{ts}")
        os.makedirs(save, exist_ok=True)
        search = os.path.join(get_image_directory(), "**", "*.png")

        self.result_table.setRowCount(0)
        self._result_row = 0
        self._append_log(f"[ui] save dir = {save}")
        self._append_log(f"[ui] running {len(cases)} checked case(s)")
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)

        self._worker = NewTestWorker(cases, save, search,
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
    # Slots
    # -----------------------------------------------------------------------
    @staticmethod
    def _fail_summary(r: dict, max_items: int = 2) -> str:
        """결과 dict 에서 fail 항목 추출 → 최대 max_items 까지 요약.
        나머지는 '(+N more)' 표시. 자세한 내용은 csv 의 개별 컬럼 참조."""
        fails = []
        for m in r.get("fixed_missing") or []:
            fails.append(f"Fixed: {m}")
        for x in r.get("meas_results") or []:
            if "FAIL" in x or "mismatch" in x or "≠" in x:
                fails.append(f"Meas: {x}")
        for x in r.get("ratio_results") or []:
            if "FAIL" in x or "MISSING" in x or "mismatch" in x or "≠" in x:
                fails.append(f"Ratio: {x}")
        for x in r.get("timestamp_results") or []:
            if "FAIL" in x or "mismatch" in x:
                fails.append(f"TS: {x}")
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
        # overall 색상은 컬럼 2 (Overall)
        if overall == "PASS":
            self.result_table.item(row, 2).setForeground(Qt.GlobalColor.darkGreen)
        elif overall in ("FAIL", "ERROR"):
            self.result_table.item(row, 2).setForeground(Qt.GlobalColor.red)
        elif overall == "INIT":
            self.result_table.item(row, 2).setForeground(Qt.GlobalColor.darkBlue)
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
