import threading

from time import sleep

from PyQt5.QtCore import Qt, QSize, QThread,pyqtSignal
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QApplication, QFrame, QWidget, QTreeWidgetItem

from qfluentwidgets import (NavigationItemPosition, MessageBox, MSFluentTitleBar, MSFluentWindow,
                            TabBar, SubtitleLabel, setFont, PrimaryPushButton, IconWidget,
                            TransparentDropDownToolButton, IndeterminateProgressRing, setTheme, TreeWidget)
from qfluentwidgets import FluentIcon as FIF
from device_interface import DevWidget

class TabInterface(QFrame):
    def __init__(self, objectName, parent=None):
        super().__init__(parent=parent)
        from main import SLE
        self.sle_entity:SLE = parent.sle_entity
        self.layout = QHBoxLayout(self)
        self.setObjectName(objectName)
        self.create_scan_widget()
        self.home_signal = HOME_SIGNAL()
        self.home_signal.signal.connect(self.receive_home_signal)
        self.sle_entity.ut_thread = 1
        server_dic = {
            0x03: None,
            0x0b: None,
            "RSSI": -50,
            "MAC": "110022003300",
            'conn_id': 0x00,
            'handle': 0x0003,
            'Type': 0x00,
            'connect': False,
        }
        self.insert_item(server_dic)
        self.sle_entity.ut._SLE_SERVER_LIST.append(server_dic)

    def create_scan_widget(self):
        self.device_vbox = QVBoxLayout()
        self.device_vbox.setAlignment(Qt.AlignLeft)
        self.device_vbox.addStretch(0)

        self.tree = TreeWidget(self)
        self.tree.setFixedSize(270, 700)
        self.device_vbox.addWidget(self.tree,0, Qt.AlignTop)
        self.tree.setHeaderHidden(True)

        self.button_vbox = QVBoxLayout()
        self.button_vbox.setAlignment(Qt.AlignTop)
        self.button_vbox.addStretch(0)

        self.spinner = IndeterminateProgressRing(self)
        self.spinner.setFixedSize(30, 30)
        self.spinner.hide()
        
        self.button_vbox.addWidget(self.spinner, 0, Qt.AlignTop|Qt.AlignHCenter)
        self.scan_button = PrimaryPushButton(FIF.SYNC, '扫描',self)
        self.scan_button.setFixedSize(150, 30)
        self.scan_button.clicked.connect(self.scan_button_clicked)
        self.button_vbox.addWidget(self.scan_button, 0, Qt.AlignTop)
        
        self.open_button = PrimaryPushButton(FIF.PLAY, '连接',self)
        self.open_button.setFixedSize(150, 30)
        self.open_button.clicked.connect(self.open_button_clicked)
        self.button_vbox.addWidget(self.open_button, 1, Qt.AlignTop)
        
        self.layout.addLayout(self.device_vbox)
        self.layout.addLayout(self.button_vbox)
        self.layout.addStretch(1)

    def open_button_clicked(self):
        if self.sle_entity.ut_thread == None:
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
                        MAC = index.parent().parent().data()[4:16]
                else:
                    MAC = index.parent().data()[4:16]
            else:
                MAC = index.data()[4:16]

            if MAC == None:
                return
            mac = []
            for i in range(0,len(MAC),2):
                mac.append(int(MAC[i:i+2], 16))
            parent = self.parentWidget().parentWidget().parentWidget().parentWidget()
            parent.addSubInterface(DevWidget(MAC,parent=parent), FIF.TAG, MAC, position=NavigationItemPosition.TOP)
            self.sle_entity.ut.sle_connect_server(mac)

    def scan_done(self):
        self.scan_button.setText("扫描")
        self.spinner.hide()

    def receive_home_signal(self,type):
        for sle_device in self.sle_entity.ut._SLE_SERVER_LIST:
            device_items = self.tree.findItems(sle_device["MAC"], Qt.MatchContains)
            if len(device_items) == 0 :
                self.insert_item(sle_device)
            else:
                device_item = device_items[0]
                device_item.setText(0, self.tr("MAC:"+sle_device["MAC"]+ "     RSSI:"+str(sle_device["RSSI"])))
                if sle_device[0x03] != None:
                    device_item.child(0).child(0).setText(0, self.tr("DATA:"+sle_device[0x03]))
                else:
                    device_item.child(0).child(0).setText(0, self.tr("DATA:"+"None"))
                if sle_device[0x0B] != None:
                    device_item.child(1).child(0).setText(0, self.tr("DATA:"+sle_device[0x0B]))
                else:
                    device_item.child(1).child(0).setText(0, self.tr("DATA:"+"None"))

    def scan_data_handle_thread(self):
        while self.spinner.isVisible():
            self.home_signal.start()
            sleep(0.2)

    def scan_button_clicked(self):
        if self.sle_entity.ut_thread == None:
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
        else:
            if self.scan_button.text() == "取消扫描":
                self.scan_button.setText("扫描")
                self.spinner.hide()
                self.sle_entity.sle_scan_done()
                self.sdh_thread.join()
            else:
                self.clear_item()
                self.scan_button.setText("取消扫描")
                self.spinner.show()
                self.sle_entity.sle_start_scan()
                self.sdh_thread = threading.Thread(target=self.scan_data_handle_thread)
                self.sdh_thread.start()

    def insert_item(self, sle_device:dict):
        item = QTreeWidgetItem([self.tr("MAC:"+sle_device["MAC"]+ "     RSSI:"+str(sle_device["RSSI"]))])
        if sle_device[0x03] != None:
            child_item1 = QTreeWidgetItem([self.tr("TYPE:0x03")])
            child_item1.addChildren([QTreeWidgetItem([self.tr("DATA:"+sle_device[0x03])])])
            item.addChildren([child_item1,])
        else:
            child_item1 = QTreeWidgetItem([self.tr("TYPE:0x03")])
            child_item1.addChildren([QTreeWidgetItem([self.tr("DATA:"+"None")])])
            item.addChildren([child_item1,])
        if sle_device[0x0B] != None:
            child_item2 = QTreeWidgetItem([self.tr("TYPE:0x0D")])
            child_item2.addChildren([QTreeWidgetItem([self.tr("DATA:"+sle_device[0x0B])])])
            item.addChildren([child_item2,])
        else:
            child_item2 = QTreeWidgetItem([self.tr("TYPE:0x0D")])
            child_item2.addChildren([QTreeWidgetItem([self.tr("DATA:"+"None")])])
            item.addChildren([child_item2,])
        self.tree.addTopLevelItem(item)

    def clear_item(self):
        self.tree.clear()


class HOME_SIGNAL(QThread):
    signal = pyqtSignal(str)

    def run(self):
        self.signal.emit("home")