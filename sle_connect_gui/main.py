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

from home_interface import TabInterface
from log_interface import LogWidget
from help_interface import HelpWidget
from setting_interface import SetWidget
from uart import uart, uart_thread


class MainWindow(MSFluentWindow):
    def __init__(self):
        self.isMicaEnabled = False
        super().__init__()

        self.sle_entity = SLE(self)

        # create sub interface
        self.homeInterface = QStackedWidget(self, objectName='homeInterface')
        self.logInterface = LogWidget('LOG Interface', self)
        self.helpInterface = HelpWidget('Help Interface', self)
        self.settingInterface = SetWidget('Setting Interface', self)

        self.initNavigation()
        self.initWindow()

    def removeSubInterface(self, interface):
        self.navigationInterface.removeWidget(interface.objectName())

    def initNavigation(self):
        self.addSubInterface(self.homeInterface, FIF.HOME, '主页', FIF.HOME_FILL)
        self.addSubInterface(self.logInterface, FIF.APPLICATION, '日志', position=NavigationItemPosition.BOTTOM)
        self.addSubInterface(self.helpInterface, FIF.HELP, '帮助', position=NavigationItemPosition.BOTTOM)
        self.addSubInterface(self.settingInterface, FIF.SETTING, '设置', position=NavigationItemPosition.BOTTOM)

        self.scan_widget = TabInterface('扫描窗口', self)
        self.homeInterface.addWidget(self.scan_widget)
        self.navigationInterface.setCurrentItem(self.homeInterface.objectName())

    def set_title(self, title):
        self.setWindowTitle(title)

    def initWindow(self):
        self.resize(500, 750)
        self.setWindowIcon(QIcon(':/qfluentwidgets/images/logo.png'))
        self.set_title('SLE Connect（串口未连接）')

        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)

class SLE:
    def __init__(self,MainWin: MainWindow):
        self.ut = uart()
        self.Mainwin = MainWin
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
        self.Mainwin.set_title('SLE Connect（串口未连接）')

    def start_uart_thread(self,COM):
        self.ut_thread = threading.Thread(target=uart_thread, args=(self.ut,COM))
        self.ut_thread.start()
        self.ut.sn_reset()
        self.ut.sle_hearbeat()
        threading.Timer(2.0, self.heartbeat_thread).start()
        self.sle_start_scan()
        self.Mainwin.set_title('SLE Connect（串口已连接）')

if __name__ == '__main__':
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)               # 设置高DPI缩放因子舍入策略
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)                                                           # 启用高DPI缩放
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)                                                              # 使用高DPI图标
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings)                                                         # 不创建本地窗口小部件兄弟
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())