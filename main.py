import sys
import os

# ----------------------------------------------------------------------
# 실제 엔트리포인트는 python_scripts/main.py 이고, 그 아래의 models / ui /
# function / config / device 가 전부 탑 레벨 패키지로 import 된다.
# 이 파일(루트 main.py) 은 VSCode 등에서 루트에서 실행했을 때도 돌게
# 해주는 얇은 런처. import 전에 sys.path / cwd 를 맞춰야 한다.
# ----------------------------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
_SCRIPTS = os.path.join(_HERE, "python_scripts")
if os.path.isdir(_SCRIPTS):
    if _SCRIPTS not in sys.path:
        sys.path.insert(0, _SCRIPTS)
    os.chdir(_SCRIPTS)

from PySide6.QtWidgets import QApplication  # noqa: E402

from models.database import initialize_database  # noqa: E402
from ui.main_window import MainWindow  # noqa: E402


def main():
    initialize_database()

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
