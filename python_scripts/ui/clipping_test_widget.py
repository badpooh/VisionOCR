# -*- coding: utf-8 -*-
"""Clipping Test tab scaffold."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTreeWidget,
    QVBoxLayout,
    QWidget,
)


class ClippingTestWidget(QWidget):
    RESULT_HEADERS = ["#", "Name", "Overall", "Command", "Readback", "Note"]

    def __init__(self, parent=None):
        super().__init__(parent)
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
        self.btn_start.setEnabled(False)

        self.btn_stop = QPushButton("STOP")
        self.btn_stop.setProperty("cssClass", "danger")
        self.btn_stop.setMinimumWidth(80)
        self.btn_stop.setEnabled(False)

        self.btn_add_tc = QPushButton("ADD TC")
        self.btn_add_tc.setEnabled(False)

        self.btn_select_all = QPushButton("Select All")
        self.btn_select_all.setEnabled(False)

        self.btn_deselect_all = QPushButton("Deselect All")
        self.btn_deselect_all.setEnabled(False)

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
        self.result_table = QTableWidget(0, len(self.RESULT_HEADERS))
        self.result_table.setHorizontalHeaderLabels(self.RESULT_HEADERS)
        self.result_table.setAlternatingRowColors(True)
        self.result_table.verticalHeader().setVisible(False)
        self.result_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.result_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        h = self.result_table.horizontalHeader()
        widths = {0: 40, 1: 220, 2: 80, 3: 180, 4: 180}
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
