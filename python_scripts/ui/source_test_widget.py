from __future__ import annotations

import os
from datetime import datetime

from PySide6.QtCore import QThread, Signal, Slot, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from external.cmengine import CMEngine
from source_test.sequence_xlsx import load_sequence, save_sequence
from source_test.source_runner import SourceTestRunner
from ui.result_controls import ResultControlsMixin


class SourceTestWorker(QThread):
    log_line = Signal(str)
    case_status = Signal(dict)
    finished_all = Signal(dict)

    def __init__(
        self,
        cases: list[dict],
        save_dir: str,
        table_rows: list[int],
        parent=None,
    ):
        super().__init__(parent)
        self.cases = cases
        self.save_dir = save_dir
        self.table_rows = table_rows
        self._runner: SourceTestRunner | None = None

    def stop(self):
        if self._runner is not None:
            self._runner.cancel()

    def run(self):
        self._runner = SourceTestRunner(
            log_callback=lambda s: self.log_line.emit(str(s)),
            case_status_callback=self._emit_case_status,
        )
        result = self._runner.run(self.cases, self.save_dir)
        self.finished_all.emit(result)

    def _emit_case_status(self, status: dict):
        update = dict(status)
        index = int(update.get("index", -1))
        if 0 <= index < len(self.table_rows):
            update["index"] = self.table_rows[index]
        self.case_status.emit(update)


class SourceTestWidget(ResultControlsMixin, QWidget):
    """CMC-driven display function test tab."""

    COLUMNS = [
        ("selected", "Run"),
        ("tc_id", "TC_ID"),
        ("name", "Test Name"),
        ("result", "Result"),
        ("failure_summary", "Failure Summary"),
    ]

    SELECT_COLUMN = 0
    RESULT_COLUMN = 3
    SUMMARY_COLUMN = 4

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cmc = CMEngine(log_callback=self._append_log)
        self._worker: SourceTestWorker | None = None
        self._cases: list[dict] = []
        self._active_result_rows: set[int] = set()
        self._init_result_controls()
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        cmc_bar = QHBoxLayout()
        cmc_bar.setSpacing(6)
        self.btn_connect_cmc = QPushButton("Connect CMC")
        self.btn_connect_cmc.setProperty("cssClass", "primary")
        self.btn_connect_cmc.clicked.connect(self._handle_connect_cmc)

        self.btn_release_cmc = QPushButton("Disconnect/Release")
        self.btn_release_cmc.setProperty("cssClass", "danger")
        self.btn_release_cmc.clicked.connect(self._handle_release_cmc)

        self.btn_device_info = QPushButton("Device Info")
        self.btn_device_info.clicked.connect(self._handle_device_info)

        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.clicked.connect(self._handle_refresh)

        self.lbl_cmc_status = QLabel("CMC: disconnected")
        self.lbl_cmc_status.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))

        cmc_bar.addWidget(self.btn_connect_cmc)
        cmc_bar.addWidget(self.btn_release_cmc)
        cmc_bar.addWidget(self.btn_device_info)
        cmc_bar.addWidget(self.btn_refresh)
        cmc_bar.addStretch()
        cmc_bar.addWidget(self.lbl_cmc_status)
        root.addLayout(cmc_bar)

        run_bar = QHBoxLayout()
        run_bar.setSpacing(6)
        self.btn_start = QPushButton("START")
        self.btn_start.setProperty("cssClass", "primary")
        self.btn_start.clicked.connect(self._handle_start)

        self.btn_stop = QPushButton("STOP")
        self.btn_stop.setProperty("cssClass", "danger")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._handle_stop)

        self.btn_out_off = QPushButton("OUT OFF")
        self.btn_out_off.setProperty("cssClass", "danger")
        self.btn_out_off.clicked.connect(self._handle_out_off)

        self.btn_add_step = QPushButton("Add Step")
        self.btn_add_step.clicked.connect(self._handle_add_step)
        self.btn_add_step.setVisible(False)

        self.btn_delete_step = QPushButton("Delete Step")
        self.btn_delete_step.clicked.connect(self._handle_delete_step)
        self.btn_delete_step.setVisible(False)

        self.btn_load = QPushButton("Load Excel")
        self.btn_load.clicked.connect(self._handle_load_excel)

        self.btn_select_all = QPushButton("Select All")
        self.btn_select_all.clicked.connect(
            lambda: self._set_all_case_selection(True)
        )

        self.btn_clear_selection = QPushButton("Clear Selection")
        self.btn_clear_selection.clicked.connect(
            lambda: self._set_all_case_selection(False)
        )

        self.btn_save = QPushButton("Save Excel")
        self.btn_save.clicked.connect(self._handle_save_excel)

        self.btn_clear_log = QPushButton("Clear Log")
        self.btn_clear_log.clicked.connect(lambda: self.log_view.clear())

        run_bar.addWidget(self.btn_start)
        run_bar.addWidget(self.btn_stop)
        run_bar.addWidget(self.btn_out_off)
        run_bar.addWidget(self.btn_add_step)
        run_bar.addWidget(self.btn_delete_step)
        run_bar.addWidget(self.btn_load)
        run_bar.addWidget(self.btn_select_all)
        run_bar.addWidget(self.btn_clear_selection)
        run_bar.addWidget(self.btn_save)
        run_bar.addStretch()
        run_bar.addWidget(self.btn_clear_log)
        root.addLayout(run_bar)

        splitter = QSplitter(Qt.Orientation.Vertical)

        sequence_group = QGroupBox("Functional Test Cases")
        sequence_layout = QVBoxLayout(sequence_group)
        sequence_layout.setContentsMargins(4, 4, 4, 4)
        sequence_layout.addLayout(self._create_result_header())
        self.sequence_table = QTableWidget(0, len(self.COLUMNS))
        self.sequence_table.setHorizontalHeaderLabels([label for _, label in self.COLUMNS])
        self.sequence_table.setAlternatingRowColors(True)
        self.sequence_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.sequence_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.sequence_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.sequence_table.verticalHeader().setVisible(False)
        header = self.sequence_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.sequence_table.setColumnWidth(2, 260)
        sequence_layout.addWidget(self.sequence_table)
        splitter.addWidget(sequence_group)

        log_group = QGroupBox("Live Log")
        log_layout = QVBoxLayout(log_group)
        log_layout.setContentsMargins(4, 4, 4, 4)
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFont(QFont("Consolas", 9))
        self.log_view.setMaximumBlockCount(3000)
        log_layout.addWidget(self.log_view)
        splitter.addWidget(log_group)

        splitter.setSizes([360, 220])
        root.addWidget(splitter, 1)

    def _populate_table(self, cases: list[dict]):
        self.sequence_table.setRowCount(0)
        for case in cases:
            self._append_case(case)

    def _append_case(self, case: dict):
        row = self.sequence_table.rowCount()
        self.sequence_table.insertRow(row)
        selected_checkbox = QCheckBox()
        selected_checkbox.setChecked(True)
        selected_checkbox.setToolTip("Run this test case")
        checkbox_container = QWidget()
        checkbox_layout = QHBoxLayout(checkbox_container)
        checkbox_layout.setContentsMargins(0, 0, 0, 0)
        checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        checkbox_layout.addWidget(selected_checkbox)
        self.sequence_table.setCellWidget(
            row, self.SELECT_COLUMN, checkbox_container
        )

        display = {
            "tc_id": case.get("tc_id", ""),
            "name": case.get("name", ""),
            "result": "READY",
            "failure_summary": "",
        }
        for col, (key, _) in enumerate(self.COLUMNS[1:], 1):
            self.sequence_table.setItem(row, col, QTableWidgetItem(str(display.get(key, ""))))
        self._set_case_status(row, "READY")

    def _steps_from_table(self) -> list[dict]:
        return list(self._cases)

    def _selected_cases(self) -> list[tuple[int, dict]]:
        selected = []
        for row, case in enumerate(self._cases):
            checkbox = self._case_checkbox(row)
            if checkbox is not None and checkbox.isChecked():
                selected.append((row, case))
        return selected

    def _case_checkbox(self, row: int) -> QCheckBox | None:
        container = self.sequence_table.cellWidget(row, self.SELECT_COLUMN)
        return container.findChild(QCheckBox) if container is not None else None

    def _set_all_case_selection(self, checked: bool):
        for row in range(self.sequence_table.rowCount()):
            checkbox = self._case_checkbox(row)
            if checkbox is not None:
                checkbox.setChecked(checked)

    def _handle_connect_cmc(self):
        try:
            info = self._cmc.connect()
        except Exception as e:
            QMessageBox.critical(self, "CMC Connect Error", str(e))
            self._set_cmc_status(False)
            return
        self._set_cmc_status(True, info)

    def _handle_release_cmc(self):
        self._cmc.release()
        self._set_cmc_status(False)

    def _handle_device_info(self):
        info = self._cmc.device_info
        if not info:
            QMessageBox.information(self, "Device Info", "CMC is not connected.")
            return
        text = "\n".join(f"{k}: {v}" for k, v in info.items())
        QMessageBox.information(self, "Device Info", text)

    def _handle_refresh(self):
        try:
            info = self._cmc.refresh()
        except Exception as e:
            QMessageBox.warning(self, "CMC Refresh Error", str(e))
            self._set_cmc_status(False)
            return
        self._set_cmc_status(True, info)
        self._append_log("[cmc] refreshed")

    def _handle_out_off(self):
        try:
            if not self._cmc.device_locked:
                self._cmc.connect()
            self._cmc.out_off()
            self._set_cmc_status(True, self._cmc.device_info)
            self._append_log("[cmc] out:off")
        except Exception as e:
            QMessageBox.critical(self, "OUT OFF Error", str(e))

    def _handle_add_step(self):
        return

    def _handle_delete_step(self):
        return

    def _handle_load_excel(self):
        start_dir = self._config_dir()
        path, _ = QFileDialog.getOpenFileName(
            self, "Load Functional Test",
            start_dir, "Excel Files (*.xlsx);;All Files (*)",
        )
        if not path:
            return
        try:
            cases = load_sequence(path)
        except Exception as e:
            QMessageBox.critical(self, "Load Error", str(e))
            return
        self._cases = cases
        self._populate_table(cases)
        self._active_result_rows = set()
        self._reset_result_summary(0)
        self._append_log(f"[ui] loaded {len(cases)} case(s) from {os.path.basename(path)}")

    def _handle_save_excel(self):
        try:
            cases = self._steps_from_table()
        except Exception as e:
            QMessageBox.warning(self, "Invalid Test Plan", str(e))
            return
        if not cases:
            QMessageBox.warning(self, "Empty", "Load a functional test Excel first.")
            return
        default_path = os.path.join(self._config_dir(), "functional_test_plan.xlsx")
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Functional Test",
            default_path, "Excel Files (*.xlsx);;All Files (*)",
        )
        if not path:
            return
        if not path.lower().endswith(".xlsx"):
            path += ".xlsx"
        try:
            save_sequence(path, cases)
        except Exception as e:
            QMessageBox.critical(self, "Save Error", str(e))
            return
        self._append_log(f"[ui] saved {len(cases)} case(s) to {path}")

    def _handle_start(self):
        if self._worker and self._worker.isRunning():
            QMessageBox.warning(self, "Running", "Test is already running.")
            return
        if not self._cases:
            QMessageBox.warning(self, "Empty", "Load a functional test Excel first.")
            return
        selected = self._selected_cases()
        if not selected:
            QMessageBox.warning(self, "Empty", "Select at least one test case.")
            return
        table_rows = [row for row, _case in selected]
        cases = [case for _row, case in selected]

        if self._cmc.device_locked:
            self._append_log("[cmc] releasing UI lock before worker run")
            self._cmc.release()
            self._set_cmc_status(False)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        scripts = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        save_dir = os.path.join(scripts, "results", f"source_{ts}")
        os.makedirs(save_dir, exist_ok=True)

        self._append_log(f"[ui] save dir = {save_dir}")
        self._append_log(f"[ui] running {len(cases)} case(s)")
        for row in range(self.sequence_table.rowCount()):
            self._set_case_status(row, "READY")
        self._active_result_rows = set(table_rows)
        self._set_last_result_dir(save_dir)
        self._reset_result_summary(len(cases))
        self._set_running(True)

        self._worker = SourceTestWorker(cases, save_dir, table_rows)
        self._worker.log_line.connect(self._append_log)
        self._worker.case_status.connect(self._on_case_status)
        self._worker.finished_all.connect(self._on_finished)
        self._worker.start()

    def _handle_stop(self):
        if self._worker and self._worker.isRunning():
            self._worker.stop()
            self._append_log("[ui] STOP requested")

    @Slot(dict)
    def _on_case_status(self, update: dict):
        self._set_case_status(
            int(update.get("index", -1)),
            str(update.get("status") or "ERROR"),
            str(update.get("failure_summary") or ""),
        )
        self._recalculate_result_summary_from_table()

    @Slot(dict)
    def _on_finished(self, result: dict):
        self._set_running(False)
        self._worker = None
        overall = result.get("overall", "")
        error = result.get("error", "")
        self._append_log(f"[ui] finished: {overall}")
        if error:
            self._append_log(f"[ui] error: {error}")
        self._recalculate_result_summary_from_table()

    def _recalculate_result_summary_from_table(self):
        counts = {"PASS": 0, "FAIL": 0, "ERROR": 0, "OTHER": 0}
        for row in self._active_result_rows:
            item = self.sequence_table.item(row, self.RESULT_COLUMN)
            status = item.text().upper() if item is not None else ""
            if status in ("PASS", "FAIL", "ERROR"):
                counts[status] += 1
            elif status not in ("", "READY", "RUNNING"):
                counts["OTHER"] += 1
        self._set_result_summary_counts(len(self._active_result_rows), counts)

    def _set_case_status(
        self, row: int, status: str, failure_summary: str = ""
    ):
        if not 0 <= row < self.sequence_table.rowCount():
            return
        result_item = self.sequence_table.item(row, self.RESULT_COLUMN)
        summary_item = self.sequence_table.item(row, self.SUMMARY_COLUMN)
        if result_item is None or summary_item is None:
            return

        result_item.setText(status)
        result_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        summary_item.setText(failure_summary)

        color = Qt.GlobalColor.darkBlue
        if status == "PASS":
            color = Qt.GlobalColor.darkGreen
        elif status in ("FAIL", "ERROR"):
            color = Qt.GlobalColor.red
        result_item.setForeground(color)

    def _set_running(self, running: bool):
        self.btn_start.setEnabled(not running)
        self.btn_stop.setEnabled(running)
        self.btn_connect_cmc.setEnabled(not running)
        self.btn_release_cmc.setEnabled(not running)
        self.btn_refresh.setEnabled(not running)
        self.btn_load.setEnabled(not running)
        self.btn_select_all.setEnabled(not running)
        self.btn_clear_selection.setEnabled(not running)
        self.btn_save.setEnabled(not running)
        for row in range(self.sequence_table.rowCount()):
            checkbox = self._case_checkbox(row)
            if checkbox is not None:
                checkbox.setEnabled(not running)

    def _set_cmc_status(self, connected: bool, info: dict | None = None):
        if not connected:
            self.lbl_cmc_status.setText("CMC: disconnected")
            return
        info = info or {}
        serial = info.get("serial") or "connected"
        ip = info.get("ip") or ""
        self.lbl_cmc_status.setText(f"CMC: {serial} {ip}".strip())

    @staticmethod
    def _config_dir() -> str:
        scripts = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_dir = os.path.join(os.path.dirname(scripts), "config")
        os.makedirs(config_dir, exist_ok=True)
        return config_dir

    @Slot(str)
    def _append_log(self, line: str):
        self.log_view.appendPlainText(line)
