import threading
import os
import sys
import serial
import serial.tools.list_ports
from time import sleep

from PyQt5.QtCore import QThread,pyqtSignal,Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QApplication, QFrame, QStackedWidget, QLabel

from qfluentwidgets import (NavigationItemPosition,FluentWindow)
from qfluentwidgets import FluentIcon as FIF, FluentIcon

from home_interface import TabInterface
from log_interface import LogWidget
from help_interface import HelpWidget
from setting_interface import SetWidget
from uart import uart, uart_thread

path = os.path.dirname(os.path.abspath(__file__))

class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        self.titleBar
        self.sle_entity = SLE(self)
        self.navigationInterface.panel.setReturnButtonVisible(False)

        # create sub interface
        self.homeInterface = QStackedWidget(self, objectName='homeInterface')
        self.logInterface = LogWidget('LOG Interface', self)
        self.helpInterface = HelpWidget('Help Interface', self)
        self.settingInterface = SetWidget('Setting Interface', self)

        self.main_signal = SLE_SIGNAL()
        self.main_signal.signal.connect(self.receive_main_signal)

        self.initNavigation()
        self.initWindow()

    def receive_main_signal(self, text):
        self.setWindowIcon(QIcon(path+"\\resources\\"+text+".png"))
        if text == "close":
            self.settingInterface.set_connect_button_text("连接")
        else:
            self.settingInterface.set_connect_button_text("断开")

    def removeSubInterface(self, interface):
        self.navigationInterface.removeWidget(interface.objectName())

    def initNavigation(self):
        self.addSubInterface(self.homeInterface, FIF.HOME, '主页',position=NavigationItemPosition.TOP)
        self.addSubInterface(self.logInterface, FIF.APPLICATION, '日志', position=NavigationItemPosition.BOTTOM)
        self.addSubInterface(self.helpInterface, FIF.HELP, '帮助', position=NavigationItemPosition.BOTTOM)
        self.addSubInterface(self.settingInterface, FIF.SETTING, '设置', position=NavigationItemPosition.BOTTOM)

        self.scan_widget = TabInterface('扫描窗口', self)
        self.homeInterface.addWidget(self.scan_widget)
        self.navigationInterface.setCurrentItem(self.homeInterface.objectName())
    
    def initWindow(self):
        self.resize(500, 750)
        self.setWindowIcon(QIcon(path+"\\resources\\close.png"))
        self.setWindowTitle('SLE Connect')

        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)

    def closeEvent(self, event):
        for _ in self.stackedWidget.view.children():
            if hasattr(_, 'stop_thread'):
                _.stop_thread()

class SLE_SIGNAL(QThread):
    signal = pyqtSignal(str)

    def set_text(self,text):
        self.text = text

    def run(self):
        self.signal.emit(self.text)

class SLE:
    def __init__(self,MainWin: MainWindow):
        self.ut = uart(self.sle_rec_data_cb)
        self.Mainwin = MainWin
        self.ut_thread = None
        self.__heartbeat_count = 0

    def sle_rec_data_cb(self,mac,data):
        for _ in self.Mainwin.stackedWidget.view.children():
            if _.objectName() == mac:
                _.text_edit_append('收<-'+data)
                break

    def heartbeat_thread(self):
        if self.ut._connect:
            self.ut.sle_hearbeat()
            self.ut._connect = False
            threading.Timer(30, self.heartbeat_thread).start()
            self.__heartbeat_count = 0
        elif self.__heartbeat_count > 3:
            self.stop_uart_thread()
        else:
            self.__heartbeat_count += 1
            threading.Timer(1, self.heartbeat_thread).start()

    def sle_scan_done(self):
        self.ut.sle_scan_device(0)
        self.Mainwin.scan_widget.scan_done()

    def sle_start_scan(self):
        self.ut.sle_scan_device(1)
        threading.Timer(15, self.sle_scan_done).start()

    def stop_uart_thread(self):
        self.ut.close()
        if self.ut_thread:
            self.ut_thread.join()
            self.ut_thread = None
        self.Mainwin.main_signal.set_text("close")
        self.Mainwin.main_signal.start()

    def check_ut_thread(self):
        if not self.ut_thread.is_alive():
            self.stop_uart_thread()

    def start_uart_thread(self,COM):
        self.ut_thread = threading.Thread(target=uart_thread, args=(self.ut,COM))
        self.ut_thread.start()
        self.ut.sle_uart_data_clear()
        self.ut.sn_reset()
        self.ut.sle_hearbeat()
        threading.Timer(1.0, self.heartbeat_thread).start()
        self.Mainwin.main_signal.set_text("open")
        self.Mainwin.main_signal.start()
        threading.Timer(0.01,self.check_ut_thread).start()

if __name__ == '__main__':
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)               # 设置高DPI缩放因子舍入策略
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)                                                           # 启用高DPI缩放
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)                                                              # 使用高DPI图标
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings)                                                         # 不创建本地窗口小部件兄弟
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())