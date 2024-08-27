import threading
from time import sleep

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QFrame, QButtonGroup

from qfluentwidgets import (QColor,TextEdit, PrimaryPushButton,IndeterminateProgressRing, SubtitleLabel, LineEdit, RadioButton)
from qfluentwidgets import FluentIcon as FIF

class DevWidget(QFrame):
    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        from main import SLE
        self.sle_entity:SLE = parent.sle_entity
        self.hBoxLayout = QVBoxLayout(self)
        self.setObjectName(text)
        self.initWdiget()
        self.initConnWidget()
        self.create_button()
        self.mac = text
        self.scd_thread = threading.Thread(target=self.sle_connect_detecte_thread)
        self.scd_thread.start()
        self.test()

    def test(self):
        for i in range(len(self.sle_entity.ut._SLE_SERVER_LIST)):
            if self.sle_entity.ut._SLE_SERVER_LIST[i]['MAC'] == self.mac:
                self.sle_entity.ut._SLE_SERVER_LIST[i]['connect'] = True

    def initWdiget(self):
        self.spinner = IndeterminateProgressRing(self)
        self.spinner.setFixedSize(230, 230)
        self.hBoxLayout.addWidget(self.spinner, 1, Qt.AlignCenter)

    def initConnWidget(self):
        self.text_label = SubtitleLabel('通信数据', self)
        self.text_label.setTextColor(QColor(0, 191, 255))
        self.text_label.setFixedSize(100, 30)
        self.hBoxLayout.addWidget(self.text_label, 0, Qt.AlignTop|Qt.AlignCenter)
        self.text_edit = TextEdit(self)
        self.text_edit.setFixedSize(425, 230)
        self.hBoxLayout.addWidget(self.text_edit, 0, Qt.AlignCenter)

        self.user_input_label = SubtitleLabel('用户输入', self)        
        self.user_input_label.setTextColor(QColor(0, 191, 255))
        self.user_input_label.setFixedSize(100, 30)
        self.hBoxLayout.addWidget(self.user_input_label, 0, Qt.AlignCenter)

        self.user_edit = LineEdit(self)
        self.user_edit.setFixedSize(425, 45)
        self.hBoxLayout.addWidget(self.user_edit, 0, Qt.AlignCenter)

        self.send_layout = QHBoxLayout()
        self.hBoxLayout.addLayout(self.send_layout)

        self.ascii_button = RadioButton('ASCII', self)
        self.ascii_button.setFixedSize(60, 30)
        self.send_layout.addWidget(self.ascii_button, 0, Qt.AlignLeft)

        self.hex_button = RadioButton('HEX', self)
        self.hex_button.setFixedSize(60, 30)
        self.send_layout.addWidget(self.hex_button, 0, Qt.AlignLeft)

        self.button_group = QButtonGroup(self)
        self.button_group.addButton(self.ascii_button)
        self.button_group.addButton(self.hex_button)
        self.ascii_button.setChecked(True)

        self.user_send_button = PrimaryPushButton(FIF.SEND, '发送', self)
        self.user_send_button.setFixedSize(100, 30)
        self.user_send_button.clicked.connect(self.user_send_button_clicked)
        self.send_layout.addWidget(self.user_send_button, 0, Qt.AlignRight)

        self.connWidge_hide()

    def get_button_group_selected(self):
        return self.button_group.checkedButton().text()

    def user_send_button_clicked(self):
        if self.get_button_group_selected() == 'ASCII':
            data = [ord(i) for i in self.user_edit.text()]
        else:
            data = []
            text = self.user_edit.text().replace(' ', '')
            for _ in range(0,len(text),2):
                if _ == len(text) - 1:
                    data.append(int(text[_], 16))
                    break
                data.append(int(self.user_edit.text().replace(' ', '')[_:_+2], 16))
        for i in range(len(self.sle_entity.ut._SLE_SERVER_LIST)):
            if self.sle_entity.ut._SLE_SERVER_LIST[i]['MAC'] == self.mac:
                self.sle_entity.ut.sle_send_data(self.sle_entity.ut._SLE_SERVER_LIST[i]['conn_id'],self.sle_entity.ut._SLE_SERVER_LIST[i]['handle'],self.sle_entity.ut._SLE_SERVER_LIST[i]['Type'],data)

    def connWidge_hide(self):
        self.text_label.hide()
        self.text_edit.hide()
        self.user_input_label.hide()
        self.user_edit.hide()
        self.ascii_button.hide()
        self.hex_button.hide()
        self.user_send_button.hide()
    
    def connWidge_show(self):
        self.text_label.show()
        self.text_edit.show()
        self.user_input_label.show()
        self.user_edit.show()
        self.ascii_button.show()
        self.hex_button.show()
        self.user_send_button.show()

    def create_button(self):
        self.close_button = PrimaryPushButton(FIF.CLOSE, '关闭', self)
        self.close_button.setFixedSize(150, 30)
        self.close_button.clicked.connect(self.close_button_clicked)
        self.hBoxLayout.addWidget(self.close_button, 1, Qt.AlignBottom|Qt.AlignHCenter)

    def close_button_clicked(self):
        parent = self.parentWidget().parentWidget().parentWidget()
        parent.removeSubInterface(self)
        MAC = [i for i in map(lambda x: int(x, 16), self.mac.split(":"))]
        self.sle_entity.ut.sle_disconnect_server(MAC)
        self.scd_thread.join()

    def sle_connect_detecte_thread(self):
        while self.sle_entity.ut_thread:
            for device in self.sle_entity.ut._SLE_SERVER_LIST:
                if device['MAC'] == self.mac:
                    if device['connect']:
                        self.spinner.hide()
                        self.connWidge_show()
                    else:
                        self.spinner.show()
                        self.connWidge_hide()
            sleep(1)
