import threading
import sys
import serial
import serial.tools.list_ports
import inspect
import ctypes
from time import sleep
from PyQt5 import QtGui

from PyQt5.QtCore import Qt, QSize, QUrl, QPoint
from PyQt5.QtGui import QIcon, QDesktopServices, QColor
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QApplication, QFrame, QStackedWidget, QLabel

from qfluentwidgets import (NavigationItemPosition, MessageBox, MSFluentTitleBar, MSFluentWindow,
                            TabBar, SubtitleLabel, setFont, TabCloseButtonDisplayMode, IconWidget,
                            TransparentDropDownToolButton, TransparentToolButton, setTheme, Theme, isDarkTheme)
from qfluentwidgets import FluentIcon as FIF, FluentIcon
from qframelesswindow import AcrylicWindow

from home_interface import CustomTitleBar, Widget, TabInterface

class MainWindow(MSFluentWindow):

    def __init__(self):
        self.isMicaEnabled = False

        super().__init__()
        self.setTitleBar(CustomTitleBar(self))
        self.tabBar:TabBar = self.titleBar.tabBar

        # create sub interface
        self.homeInterface = QStackedWidget(self, objectName='homeInterface')
        self.logInterface = Widget('LOG Interface', self)

        self.initNavigation()
        self.initWindow()

    def initNavigation(self):
        self.addSubInterface(self.homeInterface, FIF.HOME, '主页', FIF.HOME_FILL)
        self.addSubInterface(self.logInterface, FIF.APPLICATION, '日志')

        self.navigationInterface.addItem(
            routeKey='Help',
            icon=FIF.HELP,
            text='帮助',
            onClick=self.showMessageBox,
            selectable=False,
            position=NavigationItemPosition.BOTTOM,
        )

        self.navigationInterface.setCurrentItem(self.homeInterface.objectName())

        tab = self.tabBar.addTab('扫描窗口', 'scan', FluentIcon.SYNC)
        tab.closeButton.hide()
        self.scan_widget = TabInterface('扫描窗口', self)
        self.homeInterface.addWidget(self.scan_widget)
        self.scan_widget.create_scan_widget()
        self.scan_widget.insert_item({
            0x03: None,
            0x0d: "0x01",
            "RSSI": -50,
            "MAC": "00:00:00:00:00:00",
            'conn_id': None,
            'handle': None,
            'Type': None,
            'connect': False,
        })
        self.scan_widget.insert_item({
            0x03: "None",
            0x0d: "0x01",
            "RSSI": -50,
            "MAC": "11:22:33:44:55:00",
            'conn_id': None,
            'handle': None,
            'Type': None,
            'connect': False,
        })
        self.tabBar.currentChanged.connect(self.onTabChanged)
        self.tabBar.tabCloseRequested.connect(self.onTabCloseRequested)
        self.tabBar.addButton.hide()

    def initWindow(self):
        self.resize(500, 750)
        self.setWindowIcon(QIcon(':/qfluentwidgets/images/logo.png'))
        self.setWindowTitle('SLE Connect')

        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)

    def showMessageBox(self):
        w = MessageBox(
            '支持作者🥰',
            '个人开发不易，如果这个项目帮助到了您，可以考虑请作者喝一瓶快乐水🥤。您的支持就是作者开发和维护项目的动力🚀',
            self
        )
        w.yesButton.setText('来啦老弟')
        w.cancelButton.setText('下次一定')

        if w.exec():
            print('谢谢支持')

    def onTabCloseRequested(self, index: int):
        print('onTabCloseRequested', index)
        self.tabBar.removeTab(index)

    def onTabChanged(self, index: int):
        objectName = self.tabBar.currentTab().routeKey()
        self.homeInterface.setCurrentWidget(self.findChild(TabInterface, objectName))
        self.stackedWidget.setCurrentWidget(self.homeInterface)

    def addTab(self, routeKey, text, icon):
        self.tabBar.addTab(routeKey, text, icon)
        self.homeInterface.addWidget(TabInterface(routeKey, self))

if __name__ == '__main__':
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)               # 设置高DPI缩放因子舍入策略
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)                                                           # 启用高DPI缩放
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)                                                              # 使用高DPI图标
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings)                                                         # 不创建本地窗口小部件兄弟
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())