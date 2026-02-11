# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import os
import sys
import threading
import subprocess
from collections import OrderedDict

# Qt 호환성 레이어 사용
from .utils.qt_compat import QtCore, QtGui, QWidget, QFileDialog
from .ui.dialog import Ui_Dialog
from .model.seq_item_model import *
from .api import excel
from .api import publish
from .api import collect
from .api import validate
from .api.constant import *


def show_dialog(app_instance):
    """
    Shows the main dialog window.

    Args:
        app_instance: IOManagerApp 인스턴스 또는 SGTK 앱 인스턴스
    """
    # SGTK 모드 확인
    if hasattr(app_instance, 'engine'):
        # SGTK 모드: 엔진의 show_dialog 사용
        app_instance.engine.show_dialog("IO Manager", app_instance, AppDialog)
    else:
        # 독립 실행 모드: 직접 다이얼로그 생성 및 표시
        dialog = AppDialog(app_instance)
        dialog.show()
        return dialog


class AppDialog(QWidget):
    """
    Main application dialog window
    """

    def __init__(self, app_instance=None):
        """
        Constructor

        Args:
            app_instance: IOManagerApp 인스턴스 (독립 실행 모드)
                         또는 None (SGTK 모드, current_bundle 사용)
        """
        QWidget.__init__(self)

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        # 앱 인스턴스 설정
        if app_instance is not None:
            # 독립 실행 모드
            self._app = app_instance
        else:
            # SGTK 모드 (호환성)
            try:
                import sgtk
                self._app = sgtk.platform.current_bundle()
            except ImportError:
                from python.app import get_app_instance
                self._app = get_app_instance()

        self.ui.colorspace_combo.addItems(COLORSPACE)
        self._set_colorspace()
        self.ui.select_dir.clicked.connect(self._set_path)
        self.ui.create_excel.clicked.connect(self._create_excel)
        self.ui.save_excel.clicked.connect(self._save_excel)

        self.ui.publish.clicked.connect(self._publish)
        self.ui.collect.clicked.connect(self._collect)
        self.ui.check_all_btn.clicked.connect(self._check_all)
        self.ui.uncheck_all_btn.clicked.connect(self._uncheck_all)
        self.ui.edit_excel.clicked.connect(self._open_excel)
        # self.ui.validate_excel.clicked.connect(self._validate)
        self.ui.v_timecode.clicked.connect(lambda: self._validate("timecode"))
        self.ui.v_org.clicked.connect(lambda: self._validate("org"))
        self.ui.v_src.clicked.connect(lambda: self._validate("src"))
        self.ui.v_editor.clicked.connect(lambda: self._validate("editor"))
        self.ui.edit_excel.setEnabled(False)

    def _set_colorspace(self):
        """컬러스페이스 설정을 Shotgun에서 로드합니다."""
        try:
            # AppInstance를 통해 컨텍스트와 Shotgun API 가져오기
            from python.app import get_app_instance, get_context, get_shotgun

            context = get_context()
            project = context.project
            shotgun = get_shotgun()

            if not shotgun or not project:
                print("Warning: Shotgun API or project not available")
                return

            output_info = shotgun.find_one(
                "Project",
                [['id', 'is', project['id']]],
                ['sg_colorspace', 'sg_mov_codec', 'sg_out_format', 'sg_fps', 'sg_mov_colorspace']
            )

            if output_info and output_info.get('sg_colorspace'):
                colorspace = output_info['sg_colorspace']
                if colorspace.find("ACES") != -1:
                    colorspace = "ACES - " + colorspace

                print(f"Colorspace: {colorspace}")
                self.ui.colorspace_combo.setCurrentIndex(
                    self.ui.colorspace_combo.findText(colorspace)
                )

        except Exception as e:
            print(f"Error setting colorspace: {e}")
            import traceback
            traceback.print_exc()

    def _validate(self, command):

        model = self.ui.seq_model_view.model()
        v = validate.Validate(model)
        if command == "timecode":
            v.timecode()
        if command == "org":
            v.uploade_status()
        if command == "src":
            v.check_src_version()
        if command == "editor":
            v.check_editor_shot()
        # self._save_excel()

    def _open_excel(self):
        excel_file = self.ui.excel_file_label.text()
        # command = ['libreoffice5.4','--calc','--nologo']
        command = ['et']
        command.append(excel_file)
        subprocess.Popen(command)

    def _check_all(self):

        model = self.ui.seq_model_view.model()
        if model:
            for row in range(0, model.rowCount(None)):
                index = model.createIndex(row, 0)
                model.setData(index, QtCore.Qt.Checked, QtCore.Qt.CheckStateRole)

    def _uncheck_all(self):

        model = self.ui.seq_model_view.model()
        if model:
            for row in range(0, model.rowCount(None)):
                index = model.createIndex(row, 0)
                model.setData(index, QtCore.Qt.Unchecked, QtCore.Qt.CheckStateRole)

    def _set_timecode(self, index):

        row = index.row()
        column = index.column()
        if column == MODEL_KEYS['just_in']:
            timecode_col = MODEL_KEYS['timecode_in']

        elif column == MODEL_KEYS['just_out']:
            timecode_col = MODEL_KEYS['timecode_out']
        else:
            return

        model = self.ui.seq_model_view.model()

        frame = int(model.data(index, QtCore.Qt.DisplayRole))

        index = model.createIndex(row, MODEL_KEYS["scan_path"])
        dir_name = model.data(index, QtCore.Qt.DisplayRole)

        index = model.createIndex(row, MODEL_KEYS['scan_name'])
        head = model.data(index, QtCore.Qt.DisplayRole)

        index = model.createIndex(row, MODEL_KEYS['pad'])
        frame_format = model.data(index, QtCore.Qt.DisplayRole)

        index = model.createIndex(row, MODEL_KEYS['ext'])
        tail = model.data(index, QtCore.Qt.DisplayRole)

        time_code = excel.get_time_code(dir_name, head, frame_format, frame, tail)

        index = model.createIndex(row, timecode_col)
        model.setData(index, time_code, 3)

    def _set_index_by_timecode(self, index):

        row = index.row()
        column = index.column()
        if not column in [16, 17]:
            return

    def _set_path(self):
        """
        Plate Path Select
        """
        # 프로젝트 경로 가져오기
        from config.app_config import AppConfig

        project_path = AppConfig.get_project_path()
        default_path = os.path.join(project_path, 'product', 'scan') if project_path else ''

        file_dialog = QFileDialog.getExistingDirectory(
            None,
            'Output directory',
            default_path
        )

        if file_dialog:
            self.ui.lineEdit.setText(file_dialog)

    def _create_excel(self):
        print("[PROGRESS] ========================================")
        print("[PROGRESS] _create_excel() in dialog.py START")
        print("[PROGRESS] ========================================")
        path = self.ui.lineEdit.text()
        print(f"[PROGRESS] Path: {path}")
        excel_file = excel.ExcelWriteModel.get_last_excel_file(path)
        if excel_file:
            print(f"[PROGRESS] Found existing excel file: {excel_file}")
            model = SeqTableModel(excel.ExcelWriteModel.read_excel(excel_file))
            self.ui.excel_file_label.setText(excel_file)
            self.ui.edit_excel.setEnabled(True)
        else:
            print("[PROGRESS] No existing excel file, calling excel.create_excel()")
            array = excel.create_excel(path)
            print(f"[PROGRESS] excel.create_excel() returned, array length: {len(array)}")

            # Debug: array 내용 확인
            print("[DEBUG] ========== Inspecting array contents ==========")
            if len(array) > 0:
                print(f"[DEBUG] First row has {len(array[0])} columns")
                for i, item in enumerate(array[0]):
                    print(f"[DEBUG] Column {i}: type={type(item).__name__}, value preview={str(item)[:100]}")
            print("[DEBUG] ==========================================")

            print("[PROGRESS] Creating SeqTableModel...")
            model = SeqTableModel(array)
            print("[PROGRESS] SeqTableModel created successfully")
            print("[PROGRESS] Calling model.rowCount()...")
            rows = model.rowCount(None)
            print(f"[PROGRESS] model.rowCount() returned: {rows}")
            print("[PROGRESS] Calling model.columnCount()...")
            cols = model.columnCount(None)
            print(f"[PROGRESS] model.columnCount() returned: {cols}")
            print(f"[PROGRESS] Model dimensions: {rows} x {cols}")
            self.ui.excel_file_label.setText("No Saved Status")

        print("[PROGRESS] Setting model to view...", flush=True)
        print("[PROGRESS] About to call setModel()...", flush=True)
        import sys
        sys.stdout.flush()
        self.ui.seq_model_view.setModel(model)
        print("[PROGRESS] setModel() returned successfully", flush=True)
        print("[PROGRESS] Qt is now rendering the view (may call data() methods)...")
        import time
        time.sleep(0.1)  # Give Qt time to process
        print("[PROGRESS] View rendering phase completed")
        print("[PROGRESS] Setting vertical header size...")
        self.ui.seq_model_view.verticalHeader().setDefaultSectionSize(144);
        print("[PROGRESS] Vertical header size set")
        print("[PROGRESS] Connecting dataChanged signal...")
        model.dataChanged.connect(self._set_timecode)
        print("[PROGRESS] Signal connected")
        print("[PROGRESS] _create_excel() in dialog.py COMPLETED")
        print("[PROGRESS] ========================================\n")

    def _save_excel(self):

        path = self.ui.lineEdit.text()
        excel_writer = excel.ExcelWriteModel(path)
        excel_writer.write_model_to_excel(self.ui.seq_model_view.model())
        self.ui.excel_file_label.setText(excel.ExcelWriteModel.get_last_excel_file(path))
        self.ui.edit_excel.setEnabled(True)

    def _publish(self):
        model = self.ui.seq_model_view.model()
        colorspace = str(self.ui.colorspace_combo.currentText())
        group_model = OrderedDict()
        for row in range(0, model.rowCount(None)):
            index = model.createIndex(row, 0)
            check = model.data(index, QtCore.Qt.CheckStateRole)
            if check == QtCore.Qt.CheckState.Checked:
                scan_version_index = model.createIndex(row, MODEL_KEYS['version'])
                scan_version = str(model.data(scan_version_index, QtCore.Qt.DisplayRole))
                scan_type_index = model.createIndex(row, MODEL_KEYS['type'])
                scan_type = model.data(scan_type_index, QtCore.Qt.DisplayRole)
                scan_name_index = model.createIndex(row, MODEL_KEYS['scan_name'])
                scan_name = model.data(scan_name_index, QtCore.Qt.DisplayRole)
                shot_name_index = model.createIndex(row, MODEL_KEYS['shot_name'])
                shot_name = model.data(shot_name_index, QtCore.Qt.DisplayRole)
                tag_name_index = model.createIndex(row, MODEL_KEYS['clip_tag'])
                tag_name = model.data(tag_name_index, QtCore.Qt.DisplayRole)
                dict_name = shot_name + "_" + scan_name + "_" + scan_type + "_" + scan_version
                # Python 3 호환: has_key() → in operator
                if dict_name in group_model:
                    group_model[dict_name].append(row)
                else:
                    group_model[dict_name] = []
                    group_model[dict_name].append(row)

                # # seq_source
                # else:
                #     pass

        print(group_model)  # Python 3 호환
        for value in group_model.values():
            master_input = publish.MasterInput(model, value, 'shot_name')

            opt_dpx = self.ui.mov_dpx_check.isChecked()
            opt_non_retime = self.ui.non_retime_check.isChecked()
            opt_clip = self.ui.clip_check.isChecked()
            smooth_retime = self.ui.smooth_check.isChecked()
            publish.Publish(master_input, colorspace, opt_dpx, opt_non_retime, opt_clip, smooth_retime)

    def _collect(self):
        """Collect 작업을 수행합니다."""
        model = self.ui.seq_model_view.model()
        colorspace = str(self.ui.colorspace_combo.currentText())

        # 프로젝트 경로 가져오기
        from config.app_config import AppConfig
        project_path = AppConfig.get_project_path()
        default_path = os.path.join(project_path, 'product') if project_path else ''

        collect_path = QFileDialog.getExistingDirectory(
            None,
            'Collect directory',
            default_path
        )

        if not collect_path:
            return

        group_model = OrderedDict()
        shot_group_model = OrderedDict()
        for row in range(0, model.rowCount(None)):

            index = model.createIndex(row, 0)
            check = model.data(index, QtCore.Qt.CheckStateRole)
            if check == QtCore.Qt.CheckState.Checked:
                shot_name_index = model.createIndex(row, MODEL_KEYS['shot_name'])
                shot_name = model.data(shot_name_index, QtCore.Qt.DisplayRole)
                scan_type_index = model.createIndex(row, MODEL_KEYS['type'])
                scan_type = model.data(scan_type_index, QtCore.Qt.DisplayRole)
                scan_name_index = model.createIndex(row, MODEL_KEYS['scan_name'])
                scan_name = model.data(scan_name_index, QtCore.Qt.DisplayRole)
                dict_name = scan_name + "_" + scan_type
                if shot_name:
                    dict_name = shot_name + "_" + scan_type
                    # Python 3 호환: has_key() → in operator
                    if dict_name in shot_group_model:
                        shot_group_model[dict_name].append(row)
                    else:
                        shot_group_model[dict_name] = []
                        shot_group_model[dict_name].append(row)

                else:
                    # Python 3 호환: has_key() → in operator
                    if dict_name in group_model:
                        group_model[dict_name].append(row)
                    else:
                        group_model[dict_name] = []
                        group_model[dict_name].append(row)

        for key in shot_group_model.keys():
            print(key)  # Python 3 호환
            print(shot_group_model[key])
            merge = True
            collect.Collect(model, key, shot_group_model[key], colorspace, str(collect_path), merge)

        print(group_model)  # Python 3 호환
        for key in group_model.keys():
            print(key)
            print(group_model[key])
            collect.Collect(model, key, group_model[key], colorspace, str(collect_path))
