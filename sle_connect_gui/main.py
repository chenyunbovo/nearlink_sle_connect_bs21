import threading
import sys
from uart import uart, uart_thread
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

from app.SleGui.home_interface import CustomTitleBar, Widget, TabInterface, ScanWidget

class MainWindow(MSFluentWindow):

    def __init__(self):
        self.isMicaEnabled = False

        super().__init__()
        self.setTitleBar(CustomTitleBar(self))
        self.tabBar = self.titleBar.tabBar

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

        self.navigationInterface.setCurrentItem(
            self.homeInterface.objectName())

        tab = self.tabBar.addTab('scan', '扫描窗口', FluentIcon.SYNC)
        tab.closeButton.hide()
        self.scan_widget = ScanWidget(self)
        self.homeInterface.addWidget(self.scan_widget)
        
        self.tabBar.currentChanged.connect(self.onTabChanged)
        self.tabBar.tabAddRequested.connect(self.onTabAddRequested)

    def initWindow(self):
        self.resize(1100, 750)
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

    def onTabChanged(self, index: int):
        objectName = self.tabBar.currentTab().routeKey()
        self.homeInterface.setCurrentWidget(self.findChild(TabInterface, objectName))
        self.stackedWidget.setCurrentWidget(self.homeInterface)

    def onTabAddRequested(self):
        text = f'硝子酱一级棒卡哇伊×{self.tabBar.count()}'
        self.addTab(text, text, 'resource/Smiling_with_heart.png')

    def addTab(self, routeKey, text, icon):
        self.tabBar.addTab(routeKey, text, icon)
        self.homeInterface.addWidget(TabInterface(text, icon, routeKey, self))


class SLE:
    def __init__(self):
        self.ut = uart()
        self.ut_thread = None

    def heartbeat_thread(self):
        if self.ut._connect:
            self.ut.sle_hearbeat()
            self.ut._connect = False
            threading.Timer(2, self.heartbeat_thread).start()
        else:
            self.stop_uart_thread()

    def sle_scan_done(self):
        self.ut.sle_scan_device(0)

    def sle_start_scan(self):
        self.ut.sle_scan_device(1)
        threading.Timer(15, self.sle_scan_done).start()

    def stop_uart_thread(self):
        self.ut.close()
        if self.ut_thread:
            self.ut_thread.join()
            self.ut_thread = None

    def start_uart_thread(self):
        self.ut_thread = threading.Thread(target=uart_thread, args=(self.ut,'COM31'))
        self.ut_thread.start()
        self.ut.sn_reset()
        self.ut.sle_hearbeat()
        threading.Timer(2.0, self.heartbeat_thread).start()
        self.sle_start_scan()

if __name__ == '__main__':
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)               # 设置高DPI缩放因子舍入策略
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)                                                           # 启用高DPI缩放
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)                                                              # 使用高DPI图标
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings)                                                         # 不创建本地窗口小部件兄弟
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())