import logging
import datetime
import threading
from time import sleep

from PyQt5.QtCore import Qt,QThread,pyqtSignal
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QFrame, QButtonGroup

from qfluentwidgets import (QColor, TextEdit, MessageBox, PrimaryPushButton,IndeterminateProgressRing, SubtitleLabel, LineEdit, RadioButton)
from qfluentwidgets import FluentIcon as FIF

class DevWidget(QFrame):
    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.sle_logger = logging.getLogger('sle_logger')
        from main import SLE
        self.sle_entity:SLE = parent.sle_entity
        self.dev_signal = DEV_SIGNAL()
        self.dev_signal.signal.connect(self.receive_dev_signal)
        self.dev_signal.text_edit_signal.connect(self.text_edit_append_cb)
        self.hBoxLayout = QVBoxLayout(self)
        self.setObjectName(text)
        self.initWdiget()
        self.initConnWidget()
        self.create_button()
        self.mac = text
        self.scd_thread_flag = 1
        self.scd_thread = threading.Thread(target=self.sle_connect_detecte_thread)
        self.scd_thread.start()
        self.sle_logger.info('Device: '+text+' init Success!')

    def receive_dev_signal(self, text):
        for device in self.sle_entity.ut._SLE_SERVER_LIST:
            if device['MAC'] == self.mac:
                if device['connect']:
                    self.spinner.hide()
                    self.connWidge_show()
                else:
                    self.spinner.show()
                    self.connWidge_hide()

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
        self.text_edit.setFixedSize(425, 400)
        self.hBoxLayout.addWidget(self.text_edit, 0, Qt.AlignCenter)

        self.user_input_label = SubtitleLabel('用户输入', self)        
        self.user_input_label.setTextColor(QColor(0, 191, 255))
        self.user_input_label.setFixedSize(100, 30)
        self.hBoxLayout.addWidget(self.user_input_label, 0, Qt.AlignCenter)

        self.user_edit = LineEdit(self)
        self.user_edit.setFixedSize(425, 45)
        self.hBoxLayout.addWidget(self.user_edit, 0, Qt.AlignCenter)
        self.user_edit.textEdited.connect(self.user_edit_text_cb)

        self.send_layout = QHBoxLayout()
        self.hBoxLayout.addLayout(self.send_layout)

        self.ascii_button = RadioButton('ASCII', self)
        self.ascii_button.setFixedSize(60, 30)
        self.send_layout.addWidget(self.ascii_button, 0, Qt.AlignLeft)

        self.ascii_text = ''

        self.hex_button = RadioButton('HEX', self)
        self.hex_button.setFixedSize(60, 30)
        self.send_layout.addWidget(self.hex_button, 0, Qt.AlignLeft)

        self.hex_text = ''
        self.last_button = 'ASCII'

        self.button_group = QButtonGroup(self)
        self.button_group.addButton(self.ascii_button)
        self.button_group.addButton(self.hex_button)
        self.button_group.buttonClicked.connect(self.radio_button_clicked)
        self.ascii_button.setChecked(True)

        self.user_send_button = PrimaryPushButton(FIF.SEND, '发送', self)
        self.user_send_button.setFixedSize(100, 30)
        self.user_send_button.clicked.connect(self.user_send_button_clicked)
        self.send_layout.addWidget(self.user_send_button, 0, Qt.AlignRight)

        self.connWidge_hide()

    def user_edit_text_cb(self, text):
        if self.get_button_group_selected() == 'HEX':
            if len(text) != 0:
                if text[-1] not in '0123456789ABCDEFabcdef ':
                    self.sle_logger.warning('Device[' + self.mac + ']' + ' Invalid HEX character combination("0-9","A-F","a-f"," ")!Please check!')
                    w = MessageBox(
                        '警告',
                        '不是有效HEX字符组合("0-9","A-F","a-f"," ")!',
                        self
                    )
                    w.yesButton.setText('好的')
                    w.yesButton.setFixedSize(130, 35)
                    w.cancelButton.hide()
                    if w.exec():
                        self.user_edit.setText(text[:-1])
                        return

    def radio_button_clicked(self, obj):
        if obj.text() == 'ASCII' and self.last_button == 'HEX':
            self.last_button = 'ASCII'
            self.hex_text = self.user_edit.text()
            self.user_edit.setText(self.ascii_text)
            self.sle_logger.info('Device[' + self.mac + ']' + '编码形式ASCII->HEX')
        elif obj.text() == 'HEX' and self.last_button == 'ASCII':
            self.last_button = 'HEX'
            self.ascii_text = self.user_edit.text()
            self.user_edit.setText(self.hex_text)
            self.sle_logger.info('Device[' + self.mac + ']' + '编码形式HEX->ASCII')

    def get_button_group_selected(self):
        return self.button_group.checkedButton().text()

    def user_send_button_clicked(self):
        if self.get_button_group_selected() == 'ASCII':
            try:
                data = self.user_edit.text().encode('gb2312')
                self.text_edit_append('发->'+self.user_edit.text())
            except Exception as e:
                self.sle_logger.error('Device[' + self.mac + ']' + e.args[0])
        else:
            data = []
            send_source = ''
            text = self.user_edit.text().replace(' ', '')
            for _ in range(0,len(text),2):
                if _ == len(text) - 1:
                    data.append(int(text[_], 16))
                    send_source +=' ' + hex(int(text[_], 16))
                    break
                data.append(int(self.user_edit.text().replace(' ', '')[_:_+2], 16))
                send_source +=' ' + hex(int(self.user_edit.text().replace(' ', '')[_:_+2], 16))
            self.text_edit_append('发->'+send_source)
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
        MAC = []
        for i in range(0,len(self.mac),2):
            MAC.append(int(self.mac[i:i+2], 16))
        self.sle_entity.ut.sle_disconnect_server(MAC)
        self.stop_thread()
        self.sle_logger.info('Device[' + self.mac + ']' + "Close Device!")
        self.close()

    def sle_connect_detecte_thread(self):
        while self.sle_entity.ut_thread and self.scd_thread_flag:
            self.dev_signal.set_text('dev')
            self.dev_signal.start()
            sleep(1)

    def text_edit_append_cb(self, text):
        self.text_edit.append(text)

    def text_edit_append(self, text):
        now = datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]
        text = f"[{now}]{text}"
        self.dev_signal.set_text(text)
        self.sle_logger.info('Device[' + self.mac + ']' + text)
        self.dev_signal.start()

    def stop_thread(self):
        self.sle_logger.info('Device[' + self.mac + ']' + "Stop connect thread!")
        self.scd_thread_flag = 0

class DEV_SIGNAL(QThread):
    signal = pyqtSignal(str)
    text_edit_signal = pyqtSignal(str)
    texts = []

    def set_text(self,text):
        self.texts.append(text)

    def run(self):
        if len(self.texts) != 0:
            text = self.texts.pop(0)
            if text == 'dev':
                self.signal.emit("dev")
            else:
                self.text_edit_signal.emit(self.text)
            self.start()
