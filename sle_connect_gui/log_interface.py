import os
import logging
import datetime

from PyQt5.QtCore import Qt,QThread,pyqtSignal
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QWidget, QVBoxLayout
from PyQt5.QtGui import QTextCharFormat, QColor, QTextCursor
from qfluentwidgets import TextEdit

class LogWidget(QFrame):
    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.hBoxLayout = QHBoxLayout(self)
        self.setObjectName(text)
        self.log_signal = LOG_SIGNAL()
        self.log_signal.signal.connect(self.text_edit_append_cb)
        self.init_logger()
        self.initWdiget()
        self.textFormat = QTextCharFormat()
        self.sle_logger.info('Log Interface init Success!')
        
    def initWdiget(self):
        self.text_edit = TextEdit(self)
        self.text_edit.setFixedSize(425, 700)
        self.hBoxLayout.addWidget(self.text_edit, 0, Qt.AlignCenter|Qt.AlignTop)

    def init_logger(self):
        dir_path = './log'
        if(os.path.exists(dir_path)):
            pass
        else:
            os.mkdir(dir_path)

        date = dir_path + '/' + datetime.datetime.now().strftime("%Y-%m-%d") + '.log'
        self.sle_logger = logging.getLogger('sle_logger')
        self.sle_logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler(date)
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s : %(message)s')
        fh.setFormatter(formatter)
        handler = TextboxHandler(self.log_signal)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s : %(message)s')
        handler.setFormatter(formatter)
        self.sle_logger.addHandler(handler)
        self.sle_logger.addHandler(fh)

    def text_edit_append_cb(self, level, msg):
        cursor = self.text_edit.textCursor()
        if level == 'DEBUG':
            self.textFormat.setForeground(QColor(220, 220, 220))
        elif level == 'INFO':
            self.textFormat.setForeground(QColor(0, 255, 0))
        elif level == 'WARNING':
            self.textFormat.setForeground(QColor(255, 165, 0))
        elif level == 'ERROR':
            self.textFormat.setForeground(QColor(180, 0, 0))
        cursor.mergeCharFormat(self.textFormat)
        
        cursor.insertText(msg+'\n')
        
        self.textFormat.setForeground(QColor(0, 0, 0))
        cursor.mergeCharFormat(self.textFormat)
        self.text_edit.verticalScrollBar().setValue(self.text_edit.verticalScrollBar().maximum())

class LOG_SIGNAL(QThread):
    signal = pyqtSignal(str,str)
    data = []

    def append(self, level, msg):
        self.data.append((level,msg))
        self.start()

    def run(self):
        if len(self.data) > 0:
            data = self.data.pop(0)
            self.signal.emit(data[0],data[1])

class TextboxHandler(logging.Handler):
    def __init__(self,signal):
        logging.Handler.__init__(self)
        self.signal = signal
        
    def emit(self, record):
        msg = self.format(record)
        level = record.levelname
        self.signal.append(level,msg)
