"""
프로젝트 선택 다이얼로그

Shotgun에서 프로젝트 리스트를 가져와 썸네일과 함께 표시하고,
사용자가 프로젝트를 선택할 수 있도록 합니다.
"""

import os
from typing import Optional, Dict, Any

from ..utils.qt_compat import (
    QDialog, QListWidget, QListWidgetItem, QPushButton,
    QVBoxLayout, QHBoxLayout, QLabel, QMessageBox,
    Qt, QSize, QPixmap, QImage, QColor, QPainter
)


class ProjectSelectorDialog(QDialog):
    """
    Shotgun 프로젝트 선택 다이얼로그

    프로젝트를 썸네일 그리드로 표시하고 사용자가 선택할 수 있도록 합니다.
    """

    def __init__(self, shotgun, parent=None):
        """
        Args:
            shotgun: Shotgun API 인스턴스
            parent: 부모 위젯
        """
        super(ProjectSelectorDialog, self).__init__(parent)

        self.shotgun = shotgun
        self.selected_project = None

        self._init_ui()
        self._load_projects()

    def _init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("Select Project")
        self.setModal(True)
        self.resize(900, 600)

        # 메인 레이아웃
        layout = QVBoxLayout()

        # 타이틀 레이블
        title_label = QLabel("Select a project to continue:")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px;")
        layout.addWidget(title_label)

        # 프로젝트 리스트 위젯
        self.list_widget = QListWidget()
        self.list_widget.setViewMode(QListWidget.IconMode)
        self.list_widget.setIconSize(QSize(240, 144))
        self.list_widget.setGridSize(QSize(280, 220))
        self.list_widget.setResizeMode(QListWidget.Adjust)
        self.list_widget.setMovement(QListWidget.Static)
        self.list_widget.setWordWrap(True)
        self.list_widget.setSpacing(10)

        # 더블클릭으로 선택 가능
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)

        layout.addWidget(self.list_widget)

        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.ok_button = QPushButton("OK")
        self.ok_button.setEnabled(False)  # 프로젝트 선택 전까지 비활성화
        self.ok_button.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

        # 리스트 위젯 선택 변경 이벤트
        self.list_widget.itemSelectionChanged.connect(self._on_selection_changed)

    def _load_projects(self):
        """Shotgun에서 프로젝트 리스트를 로드합니다."""
        try:
            # Shotgun에서 활성 프로젝트 조회
            filters = [['archived', 'is', False]]
            fields = ['id', 'name', 'code', 'image']
            projects = self.shotgun.find(
                'Project',
                filters,
                fields,
                order=[{'field_name': 'name', 'direction': 'asc'}]
            )

            if not projects:
                QMessageBox.warning(
                    self,
                    "No Projects Found",
                    "No active projects found in Shotgun.\n"
                    "Please check your Shotgun configuration."
                )
                # Cancel 버튼을 활성화하여 사용자가 종료할 수 있도록 함
                return

            # 프로젝트 리스트 아이템 생성
            print(f"Loading {len(projects)} projects from Shotgun...")
            for project in projects:
                self._add_project_item(project)
            print(f"Loaded {self.list_widget.count()} projects successfully")

        except Exception as e:
            import traceback
            QMessageBox.critical(
                self,
                "Error Loading Projects",
                f"Failed to load projects from Shotgun:\n{e}"
            )
            print(f"Error loading projects: {e}")
            traceback.print_exc()

    def _add_project_item(self, project: Dict[str, Any]):
        """
        프로젝트 리스트 아이템을 추가합니다.

        Args:
            project: Shotgun 프로젝트 딕셔너리
        """
        item = QListWidgetItem()

        # 프로젝트 이름 설정
        project_name = project.get('name', project.get('code', 'Unknown'))
        item.setText(project_name)

        # 프로젝트 데이터 저장
        item.setData(Qt.UserRole, project)

        # 썸네일 로드
        thumbnail = self._load_thumbnail(project)
        if thumbnail:
            item.setIcon(thumbnail)

        # 툴팁 설정
        item.setToolTip(f"{project_name}\nID: {project.get('id')}")

        self.list_widget.addItem(item)

    def _load_thumbnail(self, project: Dict[str, Any]):
        """
        프로젝트 썸네일을 로드합니다.

        Args:
            project: Shotgun 프로젝트 딕셔너리

        Returns:
            QIcon: 썸네일 아이콘 또는 플레이스홀더
        """
        from ..utils.thumbnail_loader import download_thumbnail, create_placeholder

        # 썸네일 다운로드 시도
        image_url = project.get('image')
        if image_url:
            try:
                pixmap = download_thumbnail(image_url)
                if pixmap:
                    from ..utils.qt_compat import QIcon
                    return QIcon(pixmap)
            except Exception as e:
                print(f"Error downloading thumbnail for {project.get('name')}: {e}")

        # 플레이스홀더 생성
        project_name = project.get('name', project.get('code', ''))
        pixmap = create_placeholder(project_name)
        from ..utils.qt_compat import QIcon
        return QIcon(pixmap)

    def _on_selection_changed(self):
        """리스트 선택 변경 이벤트 핸들러"""
        selected_items = self.list_widget.selectedItems()
        self.ok_button.setEnabled(len(selected_items) > 0)

    def _on_item_double_clicked(self, item: QListWidgetItem):
        """리스트 아이템 더블클릭 이벤트 핸들러"""
        self.accept()

    def accept(self):
        """OK 버튼 클릭 또는 더블클릭 시 호출"""
        selected_items = self.list_widget.selectedItems()
        if selected_items:
            self.selected_project = selected_items[0].data(Qt.UserRole)
        super(ProjectSelectorDialog, self).accept()

    def get_selected_project(self) -> Optional[Dict[str, Any]]:
        """
        선택된 프로젝트를 반환합니다.

        Returns:
            선택된 프로젝트 딕셔너리 또는 None
        """
        return self.selected_project


def show_project_selector(shotgun) -> Optional[Dict[str, Any]]:
    """
    프로젝트 선택 다이얼로그를 표시합니다.

    Args:
        shotgun: Shotgun API 인스턴스

    Returns:
        선택된 프로젝트 딕셔너리 또는 None (취소 시)
    """
    dialog = ProjectSelectorDialog(shotgun)
    result = dialog.exec_()

    if result == QDialog.Accepted:
        return dialog.get_selected_project()

    return None
