import threading

from PyQt5.QtGui import QCloseEvent
import serial
import serial.tools.list_ports
from time import sleep

from PyQt5.QtWidgets import QVBoxLayout, QFrame
from PyQt5.QtCore import  QRect,QThread,pyqtSignal,Qt

from qfluentwidgets import ComboBox, PrimaryPushButton, SubtitleLabel, SettingCardGroup, OptionsSettingCard, OptionsConfigItem
from qfluentwidgets import FluentIcon as FIF
from config import cfg

class SetWidget(QFrame):
    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.layout = QVBoxLayout(self)
        self.sle_entity = parent.sle_entity
        self.setting_signal = SETTING_SIGNAL()
        self.setting_signal.signal.connect(self.receive_setting_signal)
        self.setObjectName(text.replace(' ', '-'))
        self.initWdiget()
        self.theard_flag = 1
        self.com_selected = 'COM1'
        threading.Thread(target=self.scan_serial_port_theard).start()
    
    def receive_setting_signal(self, text):
        ports = serial.tools.list_ports.comports()
        buttons = self.comboxCard.buttonGroup.buttons()
        for i in range(len(ports)):
            if ports[i].device.upper() != 'COM1':
                index = ports[i].device[3:]
                buttons[int(index)-1].show()

        for i in range(len(self.comboxCard.texts)):
            if buttons[i].text() not in [port.device.upper() for port in ports]:
                buttons[i].hide()

    def initWdiget(self):
        self.serialGroup = SettingCardGroup(self.tr('串口'), self)

        texts = []
        for i in range(100):
            texts.append('COM'+str(i+1))

        self.comboxCard = OptionsSettingCard(
            cfg.com,
            FIF.PIN,
            self.tr('COM'),
            self.tr("选择所连接的串口"),
            texts=texts,
            parent=self.serialGroup
        )

        buttons = self.comboxCard.buttonGroup.buttons()
        for i in range(len(buttons)):
            buttons[i].hide()

        self.comboxCard.optionChanged.connect(self.com_select_cb)
        self.serialGroup.addSettingCard(self.comboxCard)
        self.layout.addWidget(self.serialGroup,0, Qt.AlignTop)

        self.connect_button = PrimaryPushButton(FIF.PLAY, '连接', self)
        self.connect_button.clicked.connect(self.connect_button_clicked)
        self.layout.addWidget(self.connect_button,1, Qt.AlignRight|Qt.AlignTop)

    def com_select_cb(self, obj:OptionsConfigItem):
        self.com_selected = self.comboxCard.texts[obj.value]

    def connect_button_clicked(self):
        if self.connect_button.text() == '连接':
            self.sle_entity.start_uart_thread(self.com_selected)
        else:
            self.sle_entity.stop_uart_thread()

    def set_connect_button_text(self, text):
        self.connect_button.setText(text)

    def scan_serial_port_theard(self):
        self.setting_signal.start()
        sleep(1.5)
        buttons = self.comboxCard.buttonGroup.buttons()
        for i in range(len(self.comboxCard.texts)):
            if buttons[i].isVisible():
                buttons[i].click()
                break
        while self.theard_flag:
            self.setting_signal.start()
            sleep(1)

    def stop_thread(self):
        self.theard_flag = 0
    
class SETTING_SIGNAL(QThread):
    signal = pyqtSignal(str)

    def run(self):
        self.signal.emit("setting")