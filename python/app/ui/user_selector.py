"""
Shotgun 유저 선택 다이얼로그

이메일 주소를 입력받아 Shotgun에서 유저를 조회하고 선택하는 다이얼로그를 제공합니다.
"""

import traceback
from typing import Optional, Dict, Any

from python.app.utils.qt_compat import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, Qt
)


class UserSelectorDialog(QDialog):
    """
    사용자 이메일을 입력받아 Shotgun에서 유저를 찾는 다이얼로그

    Args:
        shotgun: Shotgun API 인스턴스
        parent: 부모 위젯 (선택사항)
    """

    def __init__(self, shotgun, parent=None):
        super().__init__(parent)
        self._sg = shotgun
        self.selected_user = None
        self._init_ui()

    def _init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("Shotgun User Login")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setMinimumHeight(180)

        # 메인 레이아웃
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 제목 라벨
        title_label = QLabel("Enter your Shotgun email address:")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(title_label)

        # 이메일 입력 필드
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("user@example.com")
        self.email_input.setStyleSheet("padding: 8px; font-size: 13px;")
        self.email_input.returnPressed.connect(self._on_ok_clicked)
        layout.addWidget(self.email_input)

        # 상태 메시지 라벨
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setMinimumHeight(30)
        layout.addWidget(self.status_label)

        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        # Cancel 버튼
        cancel_button = QPushButton("Cancel")
        cancel_button.setMinimumWidth(100)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        # OK 버튼
        ok_button = QPushButton("OK")
        ok_button.setMinimumWidth(100)
        ok_button.setDefault(True)
        ok_button.clicked.connect(self._on_ok_clicked)
        button_layout.addWidget(ok_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

        # 포커스 설정
        self.email_input.setFocus()

    def _on_ok_clicked(self):
        """OK 버튼 클릭 또는 Enter 키 입력 시 호출"""
        if self._validate_and_find_user():
            self.accept()

    def _validate_and_find_user(self):
        """
        이메일 검증 및 Shotgun 유저 조회

        Returns:
            bool: 유저를 찾았으면 True, 아니면 False
        """
        email = self.email_input.text().strip()

        # 1. 이메일 형식 검증
        if not email or '@' not in email:
            self._show_error("Please enter a valid email address")
            self.email_input.setFocus()
            return False

        # 2. Shotgun에서 유저 찾기
        try:
            self._show_info("Searching for user...")

            filters = [['email', 'is', email]]
            fields = ['id', 'name', 'email', 'login']
            user = self._sg.find_one('HumanUser', filters, fields)

            if user:
                self.selected_user = user
                self._show_success(f"Found: {user['name']}")
                return True
            else:
                self._show_error(f"User not found with email: {email}")
                self.email_input.selectAll()
                self.email_input.setFocus()
                return False

        except Exception as e:
            error_msg = f"Shotgun query failed: {str(e)}"
            self._show_error(error_msg)
            print(f"ERROR: {traceback.format_exc()}")
            return False

    def _show_error(self, message):
        """에러 메시지 표시"""
        self.status_label.setText(message)
        self.status_label.setStyleSheet("color: #d32f2f; font-size: 12px;")

    def _show_success(self, message):
        """성공 메시지 표시"""
        self.status_label.setText(message)
        self.status_label.setStyleSheet("color: #388e3c; font-size: 12px;")

    def _show_info(self, message):
        """정보 메시지 표시"""
        self.status_label.setText(message)
        self.status_label.setStyleSheet("color: #1976d2; font-size: 12px;")

    def get_selected_user(self):
        """
        선택된 유저 반환

        Returns:
            dict: Shotgun 유저 엔티티 딕셔너리 또는 None
                  {'type': 'HumanUser', 'id': 456, 'name': '홍길동', 'email': '...'}
        """
        return self.selected_user


def show_user_selector(shotgun) -> Optional[Dict[str, Any]]:
    """
    유저 선택 다이얼로그를 표시하고 선택된 유저를 반환합니다.

    Args:
        shotgun: Shotgun API 인스턴스

    Returns:
        dict: 선택된 유저 정보 또는 None (사용자 취소)
              {'type': 'HumanUser', 'id': 456, 'name': '홍길동', 'email': 'user@example.com'}

    Example:
        >>> from python.app.api.shotgun import get_shotgun
        >>> sg = get_shotgun()
        >>> user = show_user_selector(sg)
        >>> if user:
        ...     print(f"Selected user: {user['name']} (ID: {user['id']})")
        ... else:
        ...     print("User selection cancelled")
    """
    dialog = UserSelectorDialog(shotgun)
    result = dialog.exec_()

    if result == QDialog.Accepted:
        user = dialog.get_selected_user()
        # 'type' 필드 추가 (Shotgun 엔티티 딕셔너리 표준)
        if user and 'type' not in user:
            user['type'] = 'HumanUser'
        return user

    return None  # 사용자 취소
