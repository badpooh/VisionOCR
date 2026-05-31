import sys
import os

from PySide6.QtWidgets import QApplication

from models.database import initialize_database
from ui.main_window import MainWindow


def main():
    # python_scripts 디렉토리를 작업 디렉토리로 설정
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    initialize_database()

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
