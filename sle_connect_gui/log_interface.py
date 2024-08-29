import os
import logging
import datetime

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QWidget, QVBoxLayout
from PyQt5.QtGui import QTextCharFormat, QColor, QTextCursor
from qfluentwidgets import TextEdit

class LogWidget(QFrame):
    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.hBoxLayout = QHBoxLayout(self)
        self.setObjectName(text)
        self.init_logger()
        self.initWdiget()
        self.sle_logger.debug('LogWidget init')
        self.sle_logger.info('LogWidget init')
        self.sle_logger.warning('LogWidget init')
        self.sle_logger.error('LogWidget init')

        
    def initWdiget(self):
        self.text_edit = TextEdit(self)
        self.text_edit.setFixedSize(425, 700)
        self.hBoxLayout.addWidget(self.text_edit, 0, Qt.AlignCenter|Qt.AlignTop)
        handler = TextboxHandler(self.text_edit)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s : %(message)s')
        handler.setFormatter(formatter)
        self.sle_logger.addHandler(handler)

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
        self.sle_logger.addHandler(fh)

class TextboxHandler(logging.Handler):
    def __init__(self, textbox: TextEdit):
        logging.Handler.__init__(self)
        self.textbox = textbox
        self.textFormat = QTextCharFormat()
        self.cursor = self.textbox.textCursor()
        
    def emit(self, record):
        msg = self.format(record)
        if record.levelname == 'DEBUG':
            self.textFormat.setForeground(QColor(220, 220, 220))
        elif record.levelname == 'INFO':
            self.textFormat.setForeground(QColor(0, 255, 0))
        elif record.levelname == 'WARNING':
            self.textFormat.setForeground(QColor(255, 165, 0))
        elif record.levelname == 'ERROR':
            self.textFormat.setForeground(QColor(180, 0, 0))
        self.cursor.mergeCharFormat(self.textFormat)
        
        self.cursor.insertText(msg+'\n')
        
        self.textFormat.setForeground(QColor(0, 0, 0))
        self.cursor.mergeCharFormat(self.textFormat)