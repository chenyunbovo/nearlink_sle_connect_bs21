import threading
import sys
from uart import uart, uart_thread
import serial
import serial.tools.list_ports
import inspect
import ctypes
from time import sleep
from PyQt5.QtCore import Qt, QSize,pyqtSignal,QObject,QMetaType
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QAction, QGridLayout
from qfluentwidgets import FluentIcon as FIF,TextEdit, SubtitleLabel, ComboBox,PrimaryPushButton
from qfluentwidgets import (NavigationAvatarWidget, NavigationItemPosition, MessageBox, FluentWindow,
                            SplashScreen,ScrollArea)

class main_windows(FluentWindow):
    def __init__(self):
        super().__init__()
        self.initWindow()

    def initWindow(self):
        self.setStyleSheet("ButtonView{background: rgb(255,255,255)}")      # 设置背景颜色
        self.setWindowTitle('SLE Connect')
        self.resize(960, 780)
        self.setMinimumWidth(760)
        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)
        self.show()
        QApplication.processEvents()
        self.homeInterface = home_windows(self)
        self.addSubInterface(self.homeInterface, FIF.HOME, self.tr('Home'))

class home_windows(ScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.view = QWidget(self)
        self.vBoxLayout = QVBoxLayout(self.view)

        self.__initWidget()
        # self.loadSamples()

    def __initWidget(self):
        self.view.setObjectName('view')
        self.setObjectName('homeInterface')
        # StyleSheet.HOME_INTERFACE.apply(self)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidget(self.view)
        self.setWidgetResizable(True)

        self.vBoxLayout.setContentsMargins(0, 0, 0, 36)
        self.vBoxLayout.setSpacing(40)
        # self.vBoxLayout.addWidget(self.banner)
        self.vBoxLayout.setAlignment(Qt.AlignTop)

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
    w = main_windows()
    w.show()
    sys.exit(app.exec_())