# Qt 호환성 레이어 사용
from ..utils.qt_compat import QtCore, QtGui
from ..api.constant import *
import os

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
        if not index.isValid():
            return None
        elif role == QtCore.Qt.DisplayRole :
            return self.arraydata[index.row()][index.column()]
        elif role == QtCore.Qt.EditRole:
            return self.arraydata[index.row()][index.column()]
        elif role == QtCore.Qt.CheckStateRole and index.column() == 0:
            if self.arraydata[index.row()][index.column()].isChecked():
                return QtCore.Qt.Checked
            else:
                return QtCore.Qt.Unchecked
        elif role == QtCore.Qt.DecorationRole and index.column() == 1:
            thumbnail_path = self.arraydata[index.row()][index.column()]
            print(f"[DEBUG] data() - Loading thumbnail: row={index.row()}, path={thumbnail_path}")
            if os.path.exists(thumbnail_path):
                print(f"[DEBUG] data() - Thumbnail file exists, creating QPixmap...")
                try:
                    pixmap = QtGui.QPixmap(240,144)
                    print(f"[DEBUG] data() - QPixmap created, loading image...")
                    success = pixmap.load(thumbnail_path)
                    if not success:
                        print(f"[DEBUG] data() - WARNING: Failed to load thumbnail: {thumbnail_path}")
                        return None
                    print(f"[DEBUG] data() - Image loaded, scaling...")
                    pixmap = pixmap.scaled(240, 144)
                    print(f"[DEBUG] data() - Thumbnail loaded successfully")
                    return pixmap
                except Exception as e:
                    print(f"[DEBUG] data() - ERROR loading thumbnail: {e}")
                    return None
            else:
                print(f"[DEBUG] data() - Thumbnail file does not exist: {thumbnail_path}")
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

