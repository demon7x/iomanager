# Qt 호환성 레이어 사용
from ..utils.qt_compat import QtCore, QtGui
from ..api.constant import *
import os
import sys

class SeqTableModel(QtCore.QAbstractTableModel):

    def __init__(self,array ,parent=None, *args):

        QtCore.QAbstractTableModel.__init__(self, parent, *args)
        self.arraydata = array
        self.header = list(MODEL_KEYS.keys())

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.arraydata)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return len(self.arraydata[0])

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        try:
            if role != QtCore.Qt.DisplayRole:
                return None
            if orientation == QtCore.Qt.Horizontal:
                if section < len(self.header):
                    return str(self.header[section])
            return None
        except Exception as e:
            print(f"[DEBUG] headerData() EXCEPTION: section={section}, error={e}", flush=True)
            return None

    def data(self, index, role):
        try:
            if not index.isValid():
                return None

            row = index.row()
            col = index.column()

            if role == QtCore.Qt.DisplayRole:
                if col == 0:
                    return None
                if col == 1:
                    return None
                val = self.arraydata[row][col]
                if val is None:
                    return ""
                return str(val)

            elif role == QtCore.Qt.EditRole:
                if col == 0:
                    return None
                val = self.arraydata[row][col]
                if val is None:
                    return ""
                return str(val)

            elif role == QtCore.Qt.CheckStateRole and col == 0:
                checkbox = self.arraydata[row][col]
                if checkbox.isChecked():
                    return QtCore.Qt.Checked
                else:
                    return QtCore.Qt.Unchecked

            elif role == QtCore.Qt.DecorationRole and col == 1:
                thumbnail_path = self.arraydata[row][col]
                if thumbnail_path and os.path.exists(thumbnail_path):
                    try:
                        pixmap = QtGui.QPixmap(240,144)
                        success = pixmap.load(thumbnail_path)
                        if not success:
                            return None
                        pixmap = pixmap.scaled(240, 144)
                        return pixmap
                    except Exception as e:
                        print(f"[DEBUG] data() - Thumbnail error: {e}", flush=True)
                        return None
                return None

            return None

        except Exception as e:
            print(f"[DEBUG] data() EXCEPTION: row={index.row()}, col={index.column()}, role={role}, error={e}", flush=True)
            return None

    def flags(self, index):
        try:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsUserCheckable
        except Exception:
            return QtCore.Qt.ItemIsEnabled

    def setData(self, index, value, role):
        if not index.isValid():
            return False
        if role == QtCore.Qt.CheckStateRole and index.column() == 0:
            if value == QtCore.Qt.Checked:
                self.arraydata[index.row()][index.column()].setChecked(True)
            else:
                self.arraydata[index.row()][index.column()].setChecked(False)
        else:

            self.arraydata[index.row()][index.column()] = value
        self.dataChanged.emit(index, index)
