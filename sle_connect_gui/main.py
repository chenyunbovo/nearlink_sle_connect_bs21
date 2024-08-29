import threading
import os
import sys
import logging
import serial
import serial.tools.list_ports
from time import sleep

from PyQt5.QtCore import QThread,pyqtSignal,Qt
from PyQt5.QtGui import QIcon,QFont
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
        self.sle_entity = SLE(self)
        self.navigationInterface.panel.setReturnButtonVisible(False)

        # create sub interface
        self.homeInterface = QStackedWidget(self, objectName='homeInterface')
        self.logInterface = LogWidget('LOG Interface', self)
        self.helpInterface = HelpWidget('Help Interface', self)
        self.settingInterface = SetWidget('Setting Interface', self)

        self.main_signal = SLE_SIGNAL()
        self.main_signal.signal.connect(self.receive_main_signal)
        
        self.sle_logger = logging.getLogger('sle_logger')
        self.initNavigation()
        self.initWindow()
        self.sle_logger.info('MainWindow init Success!')

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
        self.sle_logger.info('MainWindow close Success!')

class SLE_SIGNAL(QThread):
    signal = pyqtSignal(str)

    def set_text(self,text):
        self.text = text

    def run(self):
        self.signal.emit(self.text)

class SLE:
    def __init__(self,MainWin: MainWindow):
        self.sle_logger = logging.getLogger('sle_logger')
        self.ut = uart(self)
        self.Mainwin = MainWin
        self.ut_thread = None
        self.__heartbeat_count = 0
        self.sle_logger.info('SLE init Success!')

    def sle_rec_data_cb(self,mac,data):
        for _ in self.Mainwin.stackedWidget.view.children():
            if _.objectName() == mac:
                if _.get_button_group_selected() == 'ASCII':
                    data_list = []
                    for i in range(0,len(data),2):
                        data_list.append(int(data[i:i+2], 16))
                    try:
                        hex_str = ''.join([format(i, '02x') for i in data_list])
                        bytes_data = bytes.fromhex(hex_str)
                        data = bytes_data.decode('gb2312')
                    except TypeError:
                        data = ''.join([chr(i) for i in data_list])
                    _.text_edit_append('收<-'+data)
                else:
                    _.text_edit_append('收<-'+data)
                break

    def heartbeat_thread(self):
        if self.ut._connect:
            self.ut.sle_hearbeat()
            self.ut._connect = False
            threading.Timer(30, self.heartbeat_thread).start()
            self.__heartbeat_count = 0
        elif self.__heartbeat_count > 2:
            self.__heartbeat_count = 0
            self.sle_logger.info('SLE ')
            self.stop_uart_thread()
        else:
            self.__heartbeat_count += 1
            self.ut.sle_hearbeat()
            threading.Timer(1, self.heartbeat_thread).start()

    def sle_scan_done(self):
        self.sle_logger.info('SLE scan done')
        self.ut.sle_scan_device(0)
        self.Mainwin.scan_widget.scan_done()

    def sle_start_scan(self):
        self.sle_logger.info('SLE start scan')
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
        try:
            if not self.ut_thread.is_alive():
                self.stop_uart_thread()
        except Exception as e:
            self.sle_logger.error(e)
            
    def start_uart_thread(self,COM):
        self.ut_thread = threading.Thread(target=uart_thread, args=(self.ut,COM))
        self.ut_thread.start()
        self.ut.sle_uart_data_clear()
        self.ut.sn_reset()
        threading.Timer(1.0, self.heartbeat_thread).start()
        self.Mainwin.main_signal.set_text("open")
        self.Mainwin.main_signal.start()
        threading.Timer(0.01,self.check_ut_thread).start()

if __name__ == '__main__':
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)               # 设置高DPI缩放因子舍入策略
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)                                                           # 启用高DPI缩放
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)                                                              # 使用高DPI图标
    app = QApplication(sys.argv)
    default_font = QFont("Arial", 10)
    app.setFont(default_font)
    app.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings)                                                         # 不创建本地窗口小部件兄弟
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())