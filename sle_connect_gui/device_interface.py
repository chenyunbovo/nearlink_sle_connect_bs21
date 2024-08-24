# coding:utf-8
import sys
import threading
from uart import uart, uart_thread

from PyQt5 import QtGui

from PyQt5.QtCore import Qt, QSize, QUrl, QPoint
from PyQt5.QtGui import QIcon, QDesktopServices, QColor
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QApplication, QFrame, QWidget, QTreeWidgetItem

from qfluentwidgets import (NavigationItemPosition, MessageBox, MSFluentTitleBar, MSFluentWindow,
                            TabBar, SubtitleLabel, setFont, PrimaryPushButton, IconWidget,
                            TransparentDropDownToolButton, IndeterminateProgressRing, setTheme, TreeWidget)
from qfluentwidgets import FluentIcon as FIF
from qframelesswindow import AcrylicWindow

class DevWidget(QFrame):
    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.hBoxLayout = QHBoxLayout(self)
        self.setObjectName(text.replace(' ', '-'))
        self.create_button()
        
    def create_button(self):
        self.close_button = PrimaryPushButton(FIF.CLOSE, '关闭', self)
        self.close_button.setFixedSize(150, 30)
        self.close_button.clicked.connect(self.close_button_clicked)
        self.hBoxLayout.addWidget(self.close_button, 0, Qt.AlignBottom)

    def close_button_clicked(self):
        parent = self.parentWidget().parentWidget().parentWidget()
        parent.removeSubInterface(self)