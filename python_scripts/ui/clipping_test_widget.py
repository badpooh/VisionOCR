# -*- coding: utf-8 -*-
"""Clipping Test tab.

Loads an xlsx file, writes out-of-range Modbus values, and checks whether the
device clips the readback value into the expected range.
"""

from __future__ import annotations

import csv
import os
import traceback
from datetime import datetime

from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from function.func_connection import ConnectionManager
from ui.result_controls import ResultControlsMixin


class ClippingTestWorker(QThread):
    log_line = Signal(str)
    result_row = Signal(dict)
    finished_all = Signal(str)

    def __init__(
        self,
        cases: list,
        product: str = "A2700",
        base_save_path: str | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.cases = cases
        self.product = product
        self.base_save_path = base_save_path
        self._runner = None
        self._stopped = False

    def stop(self):
        self._stopped = True
        if self._runner is not None:
            self._runner.cancel()

    def run(self):
        try:
            from clipping_test.clipping_runner import ClippingRunner

            self._runner = ClippingRunner(
                log_callback=lambda line: self.log_line.emit(str(line)),
            )
            results = self._runner.run(
                cases=self.cases,
                product=self.product,
                result_callback=lambda row: self.result_row.emit(row),
            )
            self._save_results(results)
            if self._stopped:
                self.finished_all.emit("Stopped")
                return

            pass_count = sum(1 for r in results if r.get("overall") == "PASS")
            fail_count = sum(1 for r in results if r.get("overall") == "FAIL")
            error_count = sum(1 for r in results if r.get("overall") == "ERROR")
            skip_count = sum(1 for r in results if r.get("overall") == "SKIP")
            self.finished_all.emit(
                f"Done: PASS {pass_count} / FAIL {fail_count} / "
                f"ERROR {error_count} / SKIP {skip_count}"
            )
        except Exception as exc:
            traceback.print_exc()
            self.finished_all.emit(f"Error: {exc}")

    def _save_results(self, results: list[dict]):
        if not results or not self.base_save_path:
            return

        os.makedirs(self.base_save_path, exist_ok=True)
        csv_path = os.path.join(self.base_save_path, "0.summary.csv")
        try:
            with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "#",
                    "name",
                    "overall",
                    "command",
                    "readback",
                    "actual_value",
                    "expected_ok",
                    "range_ok",
                    "restored_value",
                    "error",
                    "note",
                    "product",
                    "access_doc_addr",
                    "addr_doc",
                    "words",
                    "value_type",
                    "write_value",
                    "expected_value",
                    "valid_low",
                    "valid_high",
                    "read_doc_addr",
                    "read_value_type",
                    "commit_value",
                    "settle_ms",
                    "restore_after",
                    "restore_value",
                    "case_notes",
                ])
                for result in results:
                    index = result.get("index")
                    case = {}
                    if isinstance(index, int) and 1 <= index <= len(self.cases):
                        case = self.cases[index - 1]
                    writer.writerow([
                        index if index is not None else "",
                        result.get("name", ""),
                        result.get("overall", ""),
                        result.get("command", ""),
                        result.get("readback", ""),
                        result.get("actual_value", ""),
                        result.get("expected_ok", ""),
                        result.get("range_ok", ""),
                        result.get("restored_value", ""),
                        result.get("error", ""),
                        result.get("note", ""),
                        case.get("product", ""),
                        case.get("access_doc_addr", ""),
                        case.get("addr_doc", ""),
                        case.get("words", ""),
                        case.get("value_type", ""),
                        case.get("write_value", ""),
                        case.get("expected_value", ""),
                        case.get("valid_low", ""),
                        case.get("valid_high", ""),
                        case.get("read_doc_addr", ""),
                        case.get("read_value_type", ""),
                        case.get("commit_value", ""),
                        case.get("settle_ms", ""),
                        "TRUE" if case.get("restore_after") else "",
                        case.get("restore_value", ""),
                        case.get("notes", ""),
                    ])
            self.log_line.emit(f"[save] summary csv -> {csv_path}")
        except Exception as exc:
            self.log_line.emit(f"[save] csv write failed: {exc}")


class ClippingTestWidget(ResultControlsMixin, QWidget):
    RESULT_HEADERS = ["#", "Name", "Overall", "Command", "Readback", "Note"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.conn_manager = ConnectionManager()
        self._worker: ClippingTestWorker | None = None
        self._result_row = 0
        self._init_result_controls()
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        bar = QHBoxLayout()
        bar.setSpacing(6)

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

        bar.addWidget(self.btn_start)
        bar.addWidget(self.btn_stop)
        bar.addWidget(self.btn_add_tc)
        bar.addStretch()
        bar.addWidget(self.btn_select_all)
        bar.addWidget(self.btn_deselect_all)
        bar.addWidget(self.btn_clear_log)
        root.addLayout(bar)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        tree_group = QGroupBox("Test Cases")
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
        widths = {0: 40, 1: 220, 2: 80, 3: 220, 4: 220}
        for col, width in widths.items():
            h.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)
            self.result_table.setColumnWidth(col, width)
        h.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
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

    def _config_dir(self) -> str:
        here = os.path.dirname(os.path.abspath(__file__))
        scripts = os.path.dirname(here)
        return os.path.join(os.path.dirname(scripts), "config")

    def _handle_add_tc(self):
        from clipping_test.clipping_xlsx_loader import load_clipping_cases

        product = self.conn_manager.PRODUCT or "A2700"
        config_dir = self._config_dir()
        sample_path = os.path.join(config_dir, f"clipping_test_{product.lower()}_sample.xlsx")
        default_path = os.path.join(config_dir, f"clipping_test_{product.lower()}.xlsx")
        start_path = sample_path if os.path.isfile(sample_path) else default_path
        if not os.path.isfile(start_path):
            start_path = config_dir

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Clipping Test XLSX",
            start_path,
            "Excel Files (*.xlsx);;All Files (*)",
        )
        if not path:
            return

        try:
            cases = load_clipping_cases(product, xlsx_path=path)
        except Exception as exc:
            QMessageBox.critical(self, "Load Error", f"xlsx load failed: {exc}")
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
        root.setFlags(
            root.flags()
            | Qt.ItemFlag.ItemIsUserCheckable
            | Qt.ItemFlag.ItemIsAutoTristate
        )
        root.setCheckState(0, Qt.CheckState.Checked)
        root.setFont(0, QFont("Segoe UI", 10, QFont.Weight.Bold))

        for case in cases:
            label = (
                f"{case['name']}  "
                f"[{case['addr_doc']} -> {case.get('expected_value')!r}]"
            )
            leaf = QTreeWidgetItem(root, [label])
            leaf.setFlags(leaf.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            leaf.setCheckState(0, Qt.CheckState.Checked)
            leaf.setData(0, Qt.ItemDataRole.UserRole, case)
        self.tree.expandAll()

    def _get_checked_cases(self) -> list:
        cases = []
        root = self.tree.invisibleRootItem()
        for group_idx in range(root.childCount()):
            group = root.child(group_idx)
            for child_idx in range(group.childCount()):
                leaf = group.child(child_idx)
                if leaf.checkState(0) == Qt.CheckState.Checked:
                    case = leaf.data(0, Qt.ItemDataRole.UserRole)
                    if case:
                        cases.append(case)
        return cases

    def _handle_select_all(self):
        root = self.tree.invisibleRootItem()
        for idx in range(root.childCount()):
            root.child(idx).setCheckState(0, Qt.CheckState.Checked)

    def _handle_deselect_all(self):
        root = self.tree.invisibleRootItem()
        for idx in range(root.childCount()):
            root.child(idx).setCheckState(0, Qt.CheckState.Unchecked)

    def _handle_start(self):
        if self._worker and self._worker.isRunning():
            QMessageBox.warning(self, "Running", "Already running.")
            return
        if not self.conn_manager.is_connected:
            QMessageBox.warning(
                self,
                "Connect required",
                "Connect to the device first.",
            )
            return

        cases = self._get_checked_cases()
        if not cases:
            QMessageBox.warning(
                self,
                "No selection",
                "Select at least one clipping test case.",
            )
            return

        self.result_table.setRowCount(0)
        self._result_row = 0
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        here = os.path.dirname(os.path.abspath(__file__))
        scripts = os.path.dirname(here)
        save = os.path.join(scripts, "results", f"clipping_{ts}")
        os.makedirs(save, exist_ok=True)
        self._set_last_result_dir(save)
        self._reset_result_summary(len(cases))
        self._append_log(f"[ui] save dir = {save}")
        self._append_log(f"[ui] running {len(cases)} checked case(s)")

        self.btn_start.setEnabled(False)
        self.btn_add_tc.setEnabled(False)
        self.btn_stop.setEnabled(True)

        self._worker = ClippingTestWorker(
            cases=cases,
            product=self.conn_manager.PRODUCT,
            base_save_path=save,
        )
        self._worker.log_line.connect(self._append_log)
        self._worker.result_row.connect(self._on_result)
        self._worker.finished_all.connect(self._on_finished)
        self._worker.start()

    def _handle_stop(self):
        if self._worker and self._worker.isRunning():
            self._worker.stop()
            self._append_log("[ui] STOP requested")

    @Slot(dict)
    def _on_result(self, result: dict):
        row = self._result_row
        self._result_row += 1
        self.result_table.insertRow(row)

        cells = [
            str(result.get("index", row + 1)),
            str(result.get("name", "")),
            str(result.get("overall", "")),
            str(result.get("command", "")),
            str(result.get("readback", "")),
            str(result.get("note") or result.get("error") or ""),
        ]
        for col, text in enumerate(cells):
            self.result_table.setItem(row, col, QTableWidgetItem(text))

        overall = result.get("overall")
        item = self.result_table.item(row, 2)
        if overall == "PASS":
            item.setForeground(Qt.GlobalColor.darkGreen)
        elif overall in ("FAIL", "ERROR"):
            item.setForeground(Qt.GlobalColor.red)
        elif overall == "SKIP":
            item.setForeground(Qt.GlobalColor.gray)
        self._record_result_summary(overall)
        self.result_table.scrollToBottom()

    @Slot(str)
    def _append_log(self, line: str):
        self.log_view.appendPlainText(line)

    @Slot(str)
    def _on_finished(self, message: str):
        self.btn_start.setEnabled(True)
        self.btn_add_tc.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self._worker = None
        self._append_log(f"[ui] {message}")
