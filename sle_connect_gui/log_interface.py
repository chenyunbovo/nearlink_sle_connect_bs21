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

class LogWidget(QFrame):
    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.label = SubtitleLabel(text, self)
        self.hBoxLayout = QHBoxLayout(self)

        setFont(self.label, 24)
        self.label.setAlignment(Qt.AlignCenter)
        self.hBoxLayout.addWidget(self.label, 1, Qt.AlignCenter)
        self.setObjectName(text.replace(' ', '-'))