# coding:utf-8
import sys
from PyQt5 import QtGui

from PyQt5.QtCore import Qt, QSize, QUrl, QPoint
from PyQt5.QtGui import QIcon, QDesktopServices, QColor
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QApplication, QFrame, QWidget, QListWidgetItem

from qfluentwidgets import (NavigationItemPosition, MessageBox, MSFluentTitleBar, MSFluentWindow,
                            TabBar, SubtitleLabel, setFont, TabCloseButtonDisplayMode, IconWidget,
                            TransparentDropDownToolButton, TransparentToolButton, setTheme, Theme, ListWidget)
from qfluentwidgets import FluentIcon as FIF
from qframelesswindow import AcrylicWindow


class Widget(QFrame):
    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.label = SubtitleLabel(text, self)
        self.hBoxLayout = QHBoxLayout(self)

        setFont(self.label, 24)
        self.label.setAlignment(Qt.AlignCenter)
        self.hBoxLayout.addWidget(self.label, 1, Qt.AlignCenter)
        self.setObjectName(text.replace(' ', '-'))

class TabInterface(QFrame):
    def __init__(self, objectName, parent=None):
        super().__init__(parent=parent)

        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setAlignment(Qt.AlignLeft)
        self.vBoxLayout.setSpacing(30)

        self.setObjectName(objectName)

    def create_scan_widget(self):
        self.listWidget = ListWidget(self)
        self.listWidget.setFixedSize(300, 700)
        self.vBoxLayout.addWidget(self.listWidget,1, Qt.AlignTop)

    def insert_item(self, test):
        item = QListWidgetItem(test)
        self.listWidget.addItem(item)

    def clear_item(self):
        self.listWidget.clear()

class CustomTitleBar(MSFluentTitleBar):
    def __init__(self, parent):
        super().__init__(parent)

        self.tabBar = TabBar(self)

        self.tabBar.setMovable(True)
        self.tabBar.setTabMaximumWidth(220)
        self.tabBar.setTabShadowEnabled(False)
        self.tabBar.setTabSelectedBackgroundColor(QColor(255, 255, 255, 125), QColor(255, 255, 255, 50))

        self.tabBar.tabCloseRequested.connect(self.tabBar.removeTab)
        self.tabBar.currentChanged.connect(self.tabbar_changeed)

        self.hBoxLayout.insertWidget(4, self.tabBar, 1)
        self.hBoxLayout.setStretch(5, 0)
        self.hBoxLayout.insertSpacing(6, 20)

    def canDrag(self, pos: QPoint):
        if not super().canDrag(pos):
            return False

        pos.setX(pos.x() - self.tabBar.x())
        return not self.tabBar.tabRegion().contains(pos)
    
    def tabbar_changeed(self,index):
        print(index)


