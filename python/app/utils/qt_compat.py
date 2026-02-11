"""
Qt 호환성 레이어

이 모듈은 PyQt5와 PySide2를 자동으로 선택하고,
일관된 인터페이스를 제공합니다.

사용법:
    from python.app.utils.qt_compat import QtCore, QtGui, QtWidgets
"""

import sys

# Qt 바인딩 자동 선택
_QT_BINDING = None
_QT_VERSION = None

# PyQt5 시도
try:
    from PyQt5 import QtCore, QtGui, QtWidgets
    from PyQt5.QtCore import pyqtSignal as Signal
    from PyQt5.QtCore import pyqtSlot as Slot

    _QT_BINDING = "PyQt5"
    _QT_VERSION = QtCore.QT_VERSION_STR
    print(f"Qt binding: {_QT_BINDING} {_QT_VERSION}")

except ImportError:
    # PySide2 시도
    try:
        from PySide2 import QtCore, QtGui, QtWidgets
        from PySide2.QtCore import Signal, Slot

        _QT_BINDING = "PySide2"
        _QT_VERSION = QtCore.__version__
        print(f"Qt binding: {_QT_BINDING} {_QT_VERSION}")

    except ImportError:
        # PySide6 시도
        try:
            from PySide6 import QtCore, QtGui, QtWidgets
            from PySide6.QtCore import Signal, Slot

            _QT_BINDING = "PySide6"
            _QT_VERSION = QtCore.__version__
            print(f"Qt binding: {_QT_BINDING} {_QT_VERSION}")

        except ImportError:
            # PyQt6 시도
            try:
                from PyQt6 import QtCore, QtGui, QtWidgets
                from PyQt6.QtCore import pyqtSignal as Signal
                from PyQt6.QtCore import pyqtSlot as Slot

                _QT_BINDING = "PyQt6"
                _QT_VERSION = QtCore.QT_VERSION_STR
                print(f"Qt binding: {_QT_BINDING} {_QT_VERSION}")

            except ImportError:
                raise ImportError(
                    "No Qt binding found. Please install PyQt5, PySide2, PySide6, or PyQt6.\n"
                    "Recommended: pip install PyQt5"
                )


def get_qt_binding():
    """
    현재 사용 중인 Qt 바인딩 이름을 반환합니다.

    Returns:
        str: "PyQt5", "PySide2", "PySide6", 또는 "PyQt6"
    """
    return _QT_BINDING


def get_qt_version():
    """
    현재 사용 중인 Qt 버전을 반환합니다.

    Returns:
        str: Qt 버전 문자열 (예: "5.15.2")
    """
    return _QT_VERSION


# 편의를 위한 추가 임포트
QApplication = QtWidgets.QApplication
QWidget = QtWidgets.QWidget
QMainWindow = QtWidgets.QMainWindow
QDialog = QtWidgets.QDialog
QPushButton = QtWidgets.QPushButton
QLabel = QtWidgets.QLabel
QLineEdit = QtWidgets.QLineEdit
QTextEdit = QtWidgets.QTextEdit
QComboBox = QtWidgets.QComboBox
QCheckBox = QtWidgets.QCheckBox
QRadioButton = QtWidgets.QRadioButton
QListWidget = QtWidgets.QListWidget
QListWidgetItem = QtWidgets.QListWidgetItem
QTreeWidget = QtWidgets.QTreeWidget
QTableWidget = QtWidgets.QTableWidget
QTableView = QtWidgets.QTableView
QHeaderView = QtWidgets.QHeaderView
QVBoxLayout = QtWidgets.QVBoxLayout
QHBoxLayout = QtWidgets.QHBoxLayout
QGridLayout = QtWidgets.QGridLayout
QGroupBox = QtWidgets.QGroupBox
QSplitter = QtWidgets.QSplitter
QScrollArea = QtWidgets.QScrollArea
QMessageBox = QtWidgets.QMessageBox
QFileDialog = QtWidgets.QFileDialog
QMenu = QtWidgets.QMenu
QMenuBar = QtWidgets.QMenuBar
QToolBar = QtWidgets.QToolBar
QStatusBar = QtWidgets.QStatusBar
QProgressBar = QtWidgets.QProgressBar

# QtCore 클래스들
QObject = QtCore.QObject
Qt = QtCore.Qt
QTimer = QtCore.QTimer
QThread = QtCore.QThread
QSize = QtCore.QSize
QRect = QtCore.QRect
QPoint = QtCore.QPoint
QSettings = QtCore.QSettings
QAbstractItemModel = QtCore.QAbstractItemModel
QModelIndex = QtCore.QModelIndex

# QtGui 클래스들
QIcon = QtGui.QIcon
QPixmap = QtGui.QPixmap
QImage = QtGui.QImage
QColor = QtGui.QColor
QFont = QtGui.QFont
QPalette = QtGui.QPalette
QBrush = QtGui.QBrush
QPen = QtGui.QPen
QPainter = QtGui.QPainter
QStandardItemModel = QtGui.QStandardItemModel
QStandardItem = QtGui.QStandardItem


# Qt 버전별 호환성 처리
# PySide1/Qt4 스타일 코드에서는 QtGui에 위젯 클래스가 있었음 (QtGui.QPushButton 등)
# Qt5+에서는 QtWidgets로 분리되었으므로, 기존 코드 호환성을 위해
# QtWidgets의 클래스를 QtGui에 추가합니다.
_widgets_to_patch = [
    'QApplication', 'QWidget', 'QMainWindow', 'QDialog',
    'QPushButton', 'QLabel', 'QLineEdit', 'QTextEdit',
    'QComboBox', 'QCheckBox', 'QRadioButton',
    'QListWidget', 'QListWidgetItem', 'QTreeWidget', 'QTableWidget', 'QTableView',
    'QHeaderView', 'QVBoxLayout', 'QHBoxLayout', 'QGridLayout',
    'QGroupBox', 'QSplitter', 'QScrollArea',
    'QMessageBox', 'QFileDialog',
    'QMenu', 'QMenuBar', 'QToolBar', 'QStatusBar', 'QProgressBar',
    'QSpacerItem', 'QSizePolicy', 'QAbstractItemView',
    'QStyledItemDelegate', 'QStyle', 'QAction',
]
for _name in _widgets_to_patch:
    if not hasattr(QtGui, _name) and hasattr(QtWidgets, _name):
        setattr(QtGui, _name, getattr(QtWidgets, _name))

# QAction moved from QtWidgets to QtGui in Qt6
if _QT_BINDING in ["PyQt6", "PySide6"]:
    if not hasattr(QtWidgets, 'QAction') and hasattr(QtGui, 'QAction'):
        QtWidgets.QAction = QtGui.QAction

# Qt4 호환: QApplication.UnicodeUTF8 및 translate() 4-arg 형식 지원
# PySide1/Qt4에서는 translate(context, text, disambig, encoding) 형태였으나
# Qt5+에서는 encoding 인자가 제거됨
if not hasattr(QtWidgets.QApplication, 'UnicodeUTF8'):
    QtWidgets.QApplication.UnicodeUTF8 = -1
    _original_translate = QtWidgets.QApplication.translate
    @staticmethod
    def _compat_translate(context, text, disambig=None, encoding=None):
        # encoding 인자 무시 (Qt5+에서는 항상 UTF-8)
        return _original_translate(context, text, disambig)
    QtWidgets.QApplication.translate = _compat_translate
    # QtGui에도 패치 (이미 위에서 QApplication이 QtGui에 설정됨)
    QtGui.QApplication = QtWidgets.QApplication


def load_ui(ui_file, base_instance=None):
    """
    .ui 파일을 로드합니다.

    Args:
        ui_file: UI 파일 경로
        base_instance: UI를 로드할 베이스 인스턴스 (선택사항)

    Returns:
        로드된 UI 객체
    """
    if _QT_BINDING in ["PyQt5", "PyQt6"]:
        # PyQt5/PyQt6는 uic 사용
        if _QT_BINDING == "PyQt5":
            from PyQt5 import uic
        else:
            from PyQt6 import uic
        return uic.loadUi(ui_file, base_instance)
    else:
        # PySide2/PySide6는 QUiLoader 사용
        if _QT_BINDING == "PySide2":
            from PySide2 import QtUiTools
        else:
            from PySide6 import QtUiTools
        loader = QtUiTools.QUiLoader()
        return loader.load(ui_file, base_instance)


def get_app_instance():
    """
    QApplication 인스턴스를 가져오거나 생성합니다.

    Returns:
        QApplication 인스턴스
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


# 모듈 레벨에서 export
__all__ = [
    # 메인 모듈
    'QtCore',
    'QtGui',
    'QtWidgets',
    'Signal',
    'Slot',

    # 바인딩 정보
    'get_qt_binding',
    'get_qt_version',

    # QtWidgets 클래스들
    'QApplication',
    'QWidget',
    'QMainWindow',
    'QDialog',
    'QPushButton',
    'QLabel',
    'QLineEdit',
    'QTextEdit',
    'QComboBox',
    'QCheckBox',
    'QRadioButton',
    'QListWidget',
    'QListWidgetItem',
    'QTreeWidget',
    'QTableWidget',
    'QTableView',
    'QHeaderView',
    'QVBoxLayout',
    'QHBoxLayout',
    'QGridLayout',
    'QGroupBox',
    'QSplitter',
    'QScrollArea',
    'QMessageBox',
    'QFileDialog',
    'QMenu',
    'QMenuBar',
    'QToolBar',
    'QStatusBar',
    'QProgressBar',

    # QtCore 클래스들
    'QObject',
    'Qt',
    'QTimer',
    'QThread',
    'QSize',
    'QRect',
    'QPoint',
    'QSettings',
    'QAbstractItemModel',
    'QModelIndex',

    # QtGui 클래스들
    'QIcon',
    'QPixmap',
    'QImage',
    'QColor',
    'QFont',
    'QPalette',
    'QBrush',
    'QPen',
    'QPainter',
    'QStandardItemModel',
    'QStandardItem',

    # 유틸리티 함수
    'load_ui',
    'get_app_instance',
]
