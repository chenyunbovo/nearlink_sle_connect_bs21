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

        self.layout = QHBoxLayout(self)
        self.setObjectName(objectName)

    def create_scan_widget(self):
        # 创建设备显示布局
        self.device_vbox = QVBoxLayout()
        self.device_vbox.setAlignment(Qt.AlignLeft)
        self.device_vbox.addStretch(1)

        # 创建树形控件
        self.tree = TreeWidget(self)
        self.tree.setFixedSize(270, 700)
        self.device_vbox.addWidget(self.tree,1, Qt.AlignTop)
        self.tree.setHeaderHidden(True)

        # 创建按键布局
        self.button_vbox = QVBoxLayout()
        self.button_vbox.setAlignment(Qt.AlignTop)
        self.button_vbox.addStretch(0)

        # 创建按键
        self.spinner = IndeterminateProgressRing(self)
        self.spinner.setFixedSize(30, 30)
        self.spinner.hide()
        
        self.button_vbox.addWidget(self.spinner, 0, Qt.AlignCenter)
        self.scan_button = PrimaryPushButton(FIF.SYNC, '扫描',self)
        self.scan_button.setFixedSize(150, 30)
        self.scan_button.clicked.connect(self.scan_button_clicked)
        self.button_vbox.addWidget(self.scan_button, 0, Qt.AlignTop)
        
        self.open_button = PrimaryPushButton(FIF.PLAY, '连接',self)
        self.open_button.setFixedSize(150, 30)
        self.open_button.clicked.connect(self.open_button_clicked)
        self.button_vbox.addWidget(self.open_button, 1, Qt.AlignTop)
        
        # 添加布局
        self.layout.addLayout(self.device_vbox)
        self.layout.addLayout(self.button_vbox)
        self.layout.addStretch(1)


    def open_button_clicked(self):
        if sle_entity.ut_thread == None:
            w = MessageBox(
                '警告',
                '请先打开串口再进行连接操作',
                self
            )
            w.yesButton.setText('好的')
            w.yesButton.setFixedSize(130, 35)
            w.cancelButton.hide()
            if w.exec():
                return
        elif len(self.tree.selectedIndexes()) == 0:
            w = MessageBox(
                '警告',
                '请先打开选择一个设备再进行连接操作',
                self
            )
            w.yesButton.setText('好的')
            w.cancelButton.hide()
            if w.exec():
                return
        else:
            index = self.tree.selectedIndexes()[0]
            MAC = None
            if("MAC" not in index.data()):
                if("MAC" not in index.parent().data()):
                    if("MAC" not in index.parent().parent().data()):
                        MAC = None
                    else:
                        MAC = index.parent().parent().data()[4:22]
                else:
                    MAC = index.parent().data()[4:22]
            else:
                MAC = index.data()[4:22]

            if MAC == None:
                return
            
            MAC = MAC.split(":")
            mac = [i for i in map(lambda x: int(x, 16), MAC)]
            sle_entity.ut.sle_connect_server(mac)

    def scan_done(self):
        self.scan_button.setText("扫描")
        self.spinner.hide()

    def scan_button_clicked(self):
        if self.scan_button.text() == "取消扫描":
            self.scan_timer.cancel()
            self.scan_button.setText("扫描")
            self.spinner.hide()
        else:
            self.clear_item()
            self.scan_button.setText("取消扫描")
            self.spinner.show()
            self.scan_timer = threading.Timer(15, self.scan_done)
            self.scan_timer.start()

    def insert_item(self, sle_device:dict):
        item = QTreeWidgetItem([self.tr("MAC:"+sle_device["MAC"]+ "     RSSI:"+str(sle_device["RSSI"]))])
        if sle_device[0x03] != None:
            child_item1 = QTreeWidgetItem([self.tr("TYPE:0x03")])
            child_item1.addChildren([QTreeWidgetItem([self.tr("DATA:"+sle_device[0x03])])])
            item.addChildren([child_item1,])
        if sle_device[0x0D] != None:
            child_item2 = QTreeWidgetItem([self.tr("TYPE:0x0D")])
            child_item2.addChildren([QTreeWidgetItem([self.tr("DATA:"+sle_device[0x0D])])])
            item.addChildren([child_item2,])
        self.tree.addTopLevelItem(item)

    def clear_item(self):
        self.tree.clear()

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

    def start_uart_thread(self,COM):
        self.ut_thread = threading.Thread(target=uart_thread, args=(self.ut,COM))
        self.ut_thread.start()
        self.ut.sn_reset()
        self.ut.sle_hearbeat()
        threading.Timer(2.0, self.heartbeat_thread).start()
        self.sle_start_scan()

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


sle_entity = SLE()