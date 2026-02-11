# Qt 호환성 레이어 사용
from ..utils.qt_compat import QtCore, QtGui
from ..api.constant import *
import os
import sys

class SeqTableModel(QtCore.QAbstractTableModel):

    def __init__(self,array ,parent=None, *args):

        QtCore.QAbstractTableModel.__init__(self, parent, *args)
        self.arraydata = array
        #self.header = ["c","Roll","Shot name","Type","Scan path","Scan Name","pad","Ext","format","Start frame","End Frame","Range","TimeCode IN","TimeCode Out","In","Out","Fr","Date"]
        self.header = MODEL_KEYS.keys()

    def rowCount(self, parent):
        return len(self.arraydata)

    def columnCount(self, parent):
        return len(self.arraydata[0])

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role != QtCore.Qt.DisplayRole:
            return None

        if orientation == QtCore.Qt.Horizontal:
            return self.header[section]


    def data(self, index, role):
        try:
            print(f"[DEBUG] data() called - row={index.row()}, col={index.column()}, role={role}", flush=True)

            if not index.isValid():
                return None

            row = index.row()
            col = index.column()

            if role == QtCore.Qt.DisplayRole:
                val = self.arraydata[row][col]
                print(f"[DEBUG] data() DisplayRole - row={row}, col={col}, type={type(val).__name__}", flush=True)
                return val

            elif role == QtCore.Qt.EditRole:
                return self.arraydata[row][col]

            elif role == QtCore.Qt.CheckStateRole and col == 0:
                checkbox = self.arraydata[row][col]
                print(f"[DEBUG] data() CheckStateRole - type={type(checkbox).__name__}", flush=True)
                if checkbox.isChecked():
                    return QtCore.Qt.Checked
                else:
                    return QtCore.Qt.Unchecked

            elif role == QtCore.Qt.DecorationRole and col == 1:
                thumbnail_path = self.arraydata[row][col]
                print(f"[DEBUG] data() DecorationRole - thumbnail: {thumbnail_path}", flush=True)
                if os.path.exists(thumbnail_path):
                    print(f"[DEBUG] data() - Loading thumbnail...", flush=True)
                    try:
                        pixmap = QtGui.QPixmap(240,144)
                        success = pixmap.load(thumbnail_path)
                        if not success:
                            print(f"[DEBUG] data() - QPixmap.load() failed for: {thumbnail_path}", flush=True)
                            return None
                        pixmap = pixmap.scaled(240, 144)
                        print(f"[DEBUG] data() - Thumbnail loaded OK", flush=True)
                        return pixmap
                    except Exception as e:
                        print(f"[DEBUG] data() - Thumbnail error: {e}", flush=True)
                        return None
                else:
                    print(f"[DEBUG] data() - Thumbnail not found: {thumbnail_path}", flush=True)
                    return None

            return None

        except Exception as e:
            print(f"[DEBUG] data() EXCEPTION: row={index.row()}, col={index.column()}, role={role}, error={e}", flush=True)
            return None

    def flags(self, index):
        #if index.column() in [ 1,2,3,14,15,0 ]:
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsUserCheckable


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
