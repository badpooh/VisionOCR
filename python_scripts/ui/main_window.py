from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton,
    QMessageBox, QGroupBox, QGridLayout, QFrame,
    QSizePolicy, QComboBox, QTabWidget,
)
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QFont

from models import config
from models.database import save_or_update_setting, load_setting
from function.func_connection import ConnectionManager
from function.func_ocr import PaddleOCRManager
from function.func_modbus import ModbusLabels
from demo_test.demo_process import image_directory, get_image_directory
from ui.setup_test_widget import SetupTestWidget
from ui.new_test_widget import NewTestWidget

# ---------------------------------------------------------------------------
# 스타일시트
# ---------------------------------------------------------------------------
STYLE_SHEET = """
QMainWindow {
    background-color: #f5f7fa;
}

/* 그룹박스 */
QGroupBox {
    font-weight: bold;
    border: 1px solid #c0c8d4;
    border-radius: 6px;
    margin-top: 10px;
    padding: 12px 8px 8px 8px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: #3a5a8c;
}

/* 버튼 공통 */
QPushButton {
    background-color: #e8edf2;
    border: 1px solid #b8c4d0;
    border-radius: 4px;
    padding: 5px 14px;
    font-size: 12px;
    min-height: 24px;
}
QPushButton:hover {
    background-color: #d0dbe8;
    border-color: #8fa4bd;
}
QPushButton:pressed {
    background-color: #b8cce0;
}
QPushButton:disabled {
    background-color: #e8e8e8;
    color: #a0a0a0;
    border-color: #d0d0d0;
}

/* 강조 버튼 (START, Connect) */
QPushButton[cssClass="primary"] {
    background-color: #4a90d9;
    color: white;
    border: 1px solid #3a7cc0;
    font-weight: bold;
}
QPushButton[cssClass="primary"]:hover {
    background-color: #3a7cc0;
}
QPushButton[cssClass="primary"]:pressed {
    background-color: #2e6aa8;
}
QPushButton[cssClass="primary"]:disabled {
    background-color: #a8c4e0;
    border-color: #90b0d0;
}

/* 위험 버튼 (STOP, Disconnect, DEL) */
QPushButton[cssClass="danger"] {
    background-color: #e05555;
    color: white;
    border: 1px solid #c44040;
    font-weight: bold;
}
QPushButton[cssClass="danger"]:hover {
    background-color: #c44040;
}
QPushButton[cssClass="danger"]:pressed {
    background-color: #a83030;
}
QPushButton[cssClass="danger"]:disabled {
    background-color: #e0a8a8;
    border-color: #d09090;
}

/* 텍스트 필드 */
QLineEdit {
    border: 1px solid #b8c4d0;
    border-radius: 4px;
    padding: 4px 8px;
    background-color: white;
    min-height: 22px;
}
QLineEdit:focus {
    border-color: #4a90d9;
}

/* 테이블 */
QTableWidget {
    border: 1px solid #c0c8d4;
    border-radius: 4px;
    gridline-color: #dce2ea;
    background-color: white;
    alternate-background-color: #f4f7fa;
    selection-background-color: #cde0f5;
    selection-color: #1a1a1a;
}
QTableWidget::item {
    padding: 4px 8px;
}
QHeaderView::section {
    background-color: #e0e8f0;
    border: none;
    border-right: 1px solid #c8d0dc;
    border-bottom: 1px solid #c8d0dc;
    padding: 6px 8px;
    font-weight: bold;
    font-size: 11px;
    color: #3a5070;
}

/* 라벨 */
QLabel {
    color: #2a3a50;
    font-size: 12px;
}

/* 구분선 */
QFrame[frameShape="4"] {
    color: #c8d0dc;
}
"""


# ---------------------------------------------------------------------------
# Worker: Modbus 연결 (QThread)
# ---------------------------------------------------------------------------
class ConnectWorker(QThread):
    result = Signal(bool, str)

    def __init__(self, conn_manager: ConnectionManager, ip: str, setup_port: int, touch_port: int,
                 product: str | None = None, parent=None):
        super().__init__(parent)
        self.conn_manager = conn_manager
        self.ip = ip
        self.setup_port = setup_port
        self.touch_port = touch_port
        self.product = product

    def run(self):
        try:
            # 제품 모델 먼저 세팅 — ROI/Modbus 주소 분기에 쓰인다
            if self.product:
                self.conn_manager.set_product(self.product)
            self.conn_manager.ip_connect(self.ip)
            self.conn_manager.tp_update(self.touch_port)
            self.conn_manager.sp_update(self.setup_port)
            self.conn_manager.start_monitoring()
            if self.conn_manager.is_connected:
                msg = "Modbus TCP 연결 및 모니터링 시작."
                if self.product:
                    msg += f" (Model: {self.conn_manager.PRODUCT})"
                self.result.emit(True, msg)
            else:
                self.result.emit(False, "Modbus TCP 연결 실패.")
        except Exception as e:
            self.result.emit(False, str(e))


class DisconnectWorker(QThread):
    result = Signal(bool, str)

    def __init__(self, conn_manager: ConnectionManager, parent=None):
        super().__init__(parent)
        self.conn_manager = conn_manager

    def run(self):
        try:
            self.conn_manager.tcp_disconnect()
            self.result.emit(True, "Modbus TCP 연결 해제.")
        except Exception as e:
            self.result.emit(False, str(e))


# ---------------------------------------------------------------------------
# 메인 윈도우
# ---------------------------------------------------------------------------
class MainWindow(QMainWindow):
    """OCR Vision App 메인 윈도우."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("OCR Vision App")
        self.resize(900, 620)
        self.setMinimumSize(700, 450)
        self.setStyleSheet(STYLE_SHEET)

        self.conn_manager = ConnectionManager()
        self._connect_worker: ConnectWorker | None = None
        self._disconnect_worker: DisconnectWorker | None = None

        self._build_ui()
        self._load_last_settings()

    # -----------------------------------------------------------------------
    # UI 구성
    # -----------------------------------------------------------------------
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(10)

        # === 상단: 연결 설정 ===
        top_layout = QHBoxLayout()
        top_layout.setSpacing(16)

        # -- Ethernet connect 그룹 --
        conn_group = QGroupBox("Ethernet connect menu")
        conn_layout = QHBoxLayout()
        conn_layout.setSpacing(8)

        self.btn_connect = QPushButton("Connect")
        self.btn_connect.setProperty("cssClass", "primary")
        self.btn_connect.clicked.connect(self._handle_connect)

        self.btn_disconnect = QPushButton("Disconnect")
        self.btn_disconnect.setProperty("cssClass", "danger")
        self.btn_disconnect.setEnabled(False)   # 초기: 미연결 상태
        self.btn_disconnect.clicked.connect(self._handle_disconnect)

        conn_layout.addWidget(self.btn_connect)
        conn_layout.addWidget(self.btn_disconnect)
        conn_group.setLayout(conn_layout)
        top_layout.addWidget(conn_group)

        # -- Device 모델 선택 그룹 --
        device_group = QGroupBox("Device")
        device_layout = QHBoxLayout()
        device_layout.setSpacing(8)

        lbl_model = QLabel("Model")
        lbl_model.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))

        self.product_combo = QComboBox()
        self.product_combo.addItems(list(config.SUPPORTED_PRODUCTS))
        self.product_combo.setCurrentText(config.DEFAULT_PRODUCT)
        self.product_combo.setMinimumWidth(110)
        self.product_combo.currentTextChanged.connect(self._save_product)

        device_layout.addWidget(lbl_model)
        device_layout.addWidget(self.product_combo)
        device_group.setLayout(device_layout)
        top_layout.addWidget(device_group)

        top_layout.addStretch()

        # -- TCP/IP 설정 그리드 --
        tcp_group = QGroupBox("TCP/IP Settings")
        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(6)

        lbl_ip = QLabel("TCP/IP")
        lbl_ip.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        lbl_sp = QLabel("Setup Port")
        lbl_sp.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        lbl_tp = QLabel("Touch Port")
        lbl_tp.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))

        grid.addWidget(lbl_ip, 0, 0)
        grid.addWidget(lbl_sp, 1, 0)
        grid.addWidget(lbl_tp, 2, 0)

        self.tcp_ip_field = QLineEdit()
        self.tcp_ip_field.setPlaceholderText("192.168.0.1")
        self.tcp_ip_field.setMinimumWidth(140)
        self.tcp_ip_field.returnPressed.connect(self._save_tcp_ip)

        self.setup_port_field = QLineEdit()
        self.setup_port_field.setPlaceholderText("502")
        self.setup_port_field.setMinimumWidth(140)
        self.setup_port_field.returnPressed.connect(self._save_setup_port)

        self.touch_port_field = QLineEdit()
        self.touch_port_field.setPlaceholderText("503")
        self.touch_port_field.setMinimumWidth(140)
        self.touch_port_field.returnPressed.connect(self._save_touch_port)

        grid.addWidget(self.tcp_ip_field, 0, 1)
        grid.addWidget(self.setup_port_field, 1, 1)
        grid.addWidget(self.touch_port_field, 2, 1)

        btn_apply = QPushButton("Apply")
        btn_apply.clicked.connect(self._handle_apply_tcp)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self._handle_cancel_tcp)
        grid.addWidget(btn_apply, 1, 2)
        grid.addWidget(btn_cancel, 2, 2)

        tcp_group.setLayout(grid)
        top_layout.addWidget(tcp_group)

        root_layout.addLayout(top_layout)

        # === 구분선 ===
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        root_layout.addWidget(sep)

        # === 탭 위젯 ===
        self.tab_widget = QTabWidget()
        root_layout.addWidget(self.tab_widget, 1)

        # --- 탭: TEST (A3700N 데모 모드 + 외부소스 옵션) ---
        self.new_test_widget = NewTestWidget()
        self.tab_widget.addTab(self.new_test_widget, "TEST")

        # --- 탭: Setup Test ---
        self.setup_test_widget = SetupTestWidget()
        self.tab_widget.addTab(self.setup_test_widget, "Setup Test")

    # -----------------------------------------------------------------------
    # 설정 저장/로드
    # -----------------------------------------------------------------------
    def _load_last_settings(self):
        ip = load_setting(config.KEY_TCP_IP)
        if ip:
            self.tcp_ip_field.setText(ip)
        sp = load_setting(config.KEY_SETUP_PORT)
        if sp:
            self.setup_port_field.setText(sp)
        tp = load_setting(config.KEY_TOUCH_PORT)
        if tp:
            self.touch_port_field.setText(tp)

        # 제품 선택 복원 — 저장된 값이 지원 목록에 있을 때만 반영
        last_product = load_setting(config.KEY_PRODUCT)
        if last_product and last_product in config.SUPPORTED_PRODUCTS:
            self.product_combo.setCurrentText(last_product)

    def _save_tcp_ip(self):
        v = self.tcp_ip_field.text().strip()
        if v:
            save_or_update_setting(config.KEY_TCP_IP, v)

    def _save_setup_port(self):
        v = self.setup_port_field.text().strip()
        if v:
            save_or_update_setting(config.KEY_SETUP_PORT, v)

    def _save_touch_port(self):
        v = self.touch_port_field.text().strip()
        if v:
            save_or_update_setting(config.KEY_TOUCH_PORT, v)

    def _handle_apply_tcp(self):
        """Apply 버튼 — 현재 필드에 입력된 IP/Setup/Touch 포트를 모두 DB 에 저장.

        기존에는 returnPressed 때만 저장돼서, 값 바꾸고 Apply 만 눌러도
        DB 에 남아있던 옛날 값이 Connect 시 사용되는 문제가 있었음.
        """
        ip = self.tcp_ip_field.text().strip()
        sp = self.setup_port_field.text().strip()
        tp = self.touch_port_field.text().strip()
        if ip:
            save_or_update_setting(config.KEY_TCP_IP, ip)
        if sp:
            save_or_update_setting(config.KEY_SETUP_PORT, sp)
        if tp:
            save_or_update_setting(config.KEY_TOUCH_PORT, tp)
        print(f"[Apply] TCP/IP={ip!r} Setup={sp!r} Touch={tp!r} saved")

    def _handle_cancel_tcp(self):
        """Cancel 버튼 — 필드를 마지막 저장 값으로 복원."""
        self._load_last_settings()
        print("[Cancel] TCP/IP fields reverted to last saved values")

    def _save_product(self, product: str):
        """QComboBox currentTextChanged 콜백 — 즉시 DB에 저장."""
        if product and product in config.SUPPORTED_PRODUCTS:
            save_or_update_setting(config.KEY_PRODUCT, product)
            print(f"Saved product: {product}")

    def _selected_product(self) -> str:
        """현재 선택된 제품 모델명. 선택이 없으면 DEFAULT_PRODUCT."""
        product = self.product_combo.currentText()
        return product if product else config.DEFAULT_PRODUCT

    # -----------------------------------------------------------------------
    # 연결 / 연결 해제
    # -----------------------------------------------------------------------
    def _handle_connect(self):
        ip = load_setting(config.KEY_TCP_IP)
        setup_port_str = load_setting(config.KEY_SETUP_PORT)
        touch_port_str = load_setting(config.KEY_TOUCH_PORT)

        if not ip or not setup_port_str or not touch_port_str:
            QMessageBox.critical(self, "연결 오류", "IP 주소 또는 포트 번호가 설정되지 않았습니다.")
            return

        try:
            setup_port = int(setup_port_str)
            touch_port = int(touch_port_str)
        except ValueError:
            QMessageBox.critical(self, "설정 오류", "포트 번호가 올바르지 않습니다.")
            return

        self.btn_connect.setEnabled(False)
        self._connect_worker = ConnectWorker(
            self.conn_manager, ip, setup_port, touch_port,
            product=self._selected_product(),
        )
        self._connect_worker.result.connect(self._on_connect_result)
        self._connect_worker.start()

    @Slot(bool, str)
    def _on_connect_result(self, success: bool, message: str):
        if success:
            # 연결됨 → connect 비활성, disconnect 활성
            self.btn_connect.setEnabled(False)
            self.btn_disconnect.setEnabled(True)
            QMessageBox.information(self, "연결 상태", message)
        else:
            # 실패 → 다시 connect 활성
            self.btn_connect.setEnabled(True)
            self.btn_disconnect.setEnabled(False)
            QMessageBox.critical(self, "연결 오류", message)

    def _handle_disconnect(self):
        self.btn_disconnect.setEnabled(False)
        self._disconnect_worker = DisconnectWorker(self.conn_manager)
        self._disconnect_worker.result.connect(self._on_disconnect_result)
        self._disconnect_worker.start()

    @Slot(bool, str)
    def _on_disconnect_result(self, success: bool, message: str):
        if success:
            # 끊김 → connect 활성, disconnect 비활성
            self.btn_connect.setEnabled(True)
            self.btn_disconnect.setEnabled(False)
            QMessageBox.information(self, "연결 해제 상태", message)
        else:
            # 실패 → disconnect 다시 활성 (사용자가 재시도)
            self.btn_disconnect.setEnabled(True)
            QMessageBox.critical(self, "연결 해제 오류", message)

    # -----------------------------------------------------------------------
    # 종료 처리
    # -----------------------------------------------------------------------
    def closeEvent(self, event):
        if self.conn_manager.is_connected:
            try:
                self.conn_manager.tcp_disconnect()
            except Exception:
                pass
        event.accept()
