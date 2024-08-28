import threading

from PyQt5.QtGui import QCloseEvent
import serial
import serial.tools.list_ports
from time import sleep

from PyQt5.QtCore import  QRect,QThread,pyqtSignal
from PyQt5.QtWidgets import QFrame

from qfluentwidgets import ComboBox, PrimaryPushButton, SubtitleLabel
from qfluentwidgets import FluentIcon as FIF

class SetWidget(QFrame):
    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.sle_entity = parent.sle_entity
        self.setting_signal = SETTING_SIGNAL()
        self.setting_signal.signal.connect(self.receive_setting_signal)
        self.setObjectName(text.replace(' ', '-'))
        self.initWdiget()
        self.theard_flag = 1
        threading.Thread(target=self.scan_serial_port_theard).start()
    
    def receive_setting_signal(self, text):
        ports = serial.tools.list_ports.comports()
        for i in ports:
            if self.comboBox.findText(i.device) == -1 and i.device != 'COM1':
                self.comboBox.addItem(i.device)
        for i in range(self.comboBox.count()):
            if self.comboBox.itemText(i) not in [port.device for port in ports]:
                self.comboBox.removeItem(i)

    def initWdiget(self):
        self.com_label = SubtitleLabel("COM:", self)
        self.com_label.setGeometry(QRect(50, 50, 50, 30))
        self.comboBox = ComboBox(self)
        self.comboBox.setGeometry(QRect(120, 52, 200, 30))

        self.connect_button = PrimaryPushButton(FIF.PLAY, '连接', self)
        self.connect_button.setGeometry(QRect(160, 200, 150, 40))   
        self.connect_button.clicked.connect(self.connect_button_clicked)

    def connect_button_clicked(self):
        if self.connect_button.text() == '连接':
            self.sle_entity.start_uart_thread(self.comboBox.currentText())
        else:
            self.sle_entity.stop_uart_thread()

    def set_connect_button_text(self, text):
        self.connect_button.setText(text)

    def scan_serial_port_theard(self):
        while self.theard_flag:
            self.setting_signal.start()
            sleep(1)

    def stop_thread(self):
        self.theard_flag = 0
    
class SETTING_SIGNAL(QThread):
    signal = pyqtSignal(str)

    def run(self):
        self.signal.emit("setting")