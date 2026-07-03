from __future__ import annotations

import os

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMessageBox, QPushButton


class ResultControlsMixin:
    def _init_result_controls(self):
        self._last_result_dir = None
        self._summary_total = 0
        self._summary_counts = {"PASS": 0, "FAIL": 0, "ERROR": 0, "OTHER": 0}

    def _create_result_header(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(2, 0, 2, 0)

        self.lbl_result_summary = QLabel()
        self.lbl_result_summary.setTextFormat(Qt.TextFormat.RichText)
        self.lbl_result_summary.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )

        self.btn_open_results = QPushButton("Open Results")
        self.btn_open_results.setEnabled(False)
        self.btn_open_results.clicked.connect(self._open_last_result_dir)

        layout.addStretch()
        layout.addWidget(self.lbl_result_summary)
        layout.addWidget(self.btn_open_results)
        self._update_result_summary()
        return layout

    def _set_last_result_dir(self, path: str | None):
        self._last_result_dir = path
        if hasattr(self, "btn_open_results"):
            self.btn_open_results.setEnabled(bool(path and os.path.isdir(path)))

    def _reset_result_summary(self, total: int = 0):
        self._summary_total = max(0, int(total or 0))
        self._summary_counts = {"PASS": 0, "FAIL": 0, "ERROR": 0, "OTHER": 0}
        self._update_result_summary()

    def _record_result_summary(self, overall):
        key = str(overall or "").upper()
        if key in ("PASS", "FAIL", "ERROR"):
            self._summary_counts[key] += 1
        else:
            self._summary_counts["OTHER"] += 1
        self._update_result_summary()

    def _set_result_summary_counts(self, total: int, counts: dict):
        self._summary_total = max(0, int(total or 0))
        self._summary_counts = {
            "PASS": int(counts.get("PASS", 0) or 0),
            "FAIL": int(counts.get("FAIL", 0) or 0),
            "ERROR": int(counts.get("ERROR", 0) or 0),
            "OTHER": int(counts.get("OTHER", 0) or 0),
        }
        self._update_result_summary()

    def _update_result_summary(self):
        if not hasattr(self, "lbl_result_summary"):
            return
        done = (
            self._summary_counts["PASS"]
            + self._summary_counts["FAIL"]
            + self._summary_counts["ERROR"]
            + self._summary_counts["OTHER"]
        )
        total = max(self._summary_total, done)
        other = self._summary_counts["OTHER"]
        other_html = (
            f' <span style="color:#667085;">OTHER {other}</span>'
            if other
            else ""
        )
        self.lbl_result_summary.setText(
            '<span style="color:#344054;">'
            f"Done {done}/{total}"
            '</span>'
            ' <span style="color:#2e7d32;">PASS '
            f'{self._summary_counts["PASS"]}</span>'
            ' <span style="color:#c62828;">FAIL '
            f'{self._summary_counts["FAIL"]}</span>'
            ' <span style="color:#ef6c00;">ERROR '
            f'{self._summary_counts["ERROR"]}</span>'
            f"{other_html}"
        )

    def _open_last_result_dir(self):
        path = self._last_result_dir
        if not path or not os.path.isdir(path):
            QMessageBox.information(
                self,
                "No Results",
                "No result folder is available yet.",
            )
            return
        ok = QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.abspath(path)))
        if not ok:
            QMessageBox.warning(
                self,
                "Open Failed",
                f"Could not open result folder:\n{path}",
            )
