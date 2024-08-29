import threading
import logging
import serial
import serial.tools.list_ports
from time import sleep

from PyQt5.QtWidgets import QVBoxLayout, QFrame
from PyQt5.QtCore import QThread,pyqtSignal,Qt,QUrl
from PyQt5.QtGui import QDesktopServices

from qfluentwidgets import PrimaryPushButton, MessageBox, SettingCardGroup, OptionsSettingCard, OptionsConfigItem, PrimaryPushSettingCard
from qfluentwidgets import FluentIcon as FIF
from config import cfg, YEAR, AUTHOR, VERSION, FEEDBACK_URL

class SetWidget(QFrame):
    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.layout = QVBoxLayout(self)
        self.sle_entity = parent.sle_entity
        self.sle_logger = logging.getLogger('sle_logger')
        self.setting_signal = SETTING_SIGNAL()
        self.setting_signal.signal.connect(self.receive_setting_signal)
        self.uart_signal = UART_SIGNAL()
        self.uart_signal.error_signal.connect(self.uart_error_cb)
        self.setObjectName(text.replace(' ', '-'))
        self.initWdiget()
        self.theard_flag = 1
        self.com_selected = 'COM1'
        threading.Thread(target=self.scan_serial_port_theard).start()
        self.sle_logger.info('Setting Interface init Success!')
    
    def uart_error_cb(self, text):
        self.sle_logger.error(text)
        w = MessageBox(
            '警告',
            text,
            self
        )
        w.yesButton.setText('好的')
        w.yesButton.setFixedSize(130, 35)
        w.cancelButton.hide()
        if w.exec():
            return

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
        self.layout.addWidget(self.connect_button, 0, Qt.AlignRight|Qt.AlignTop)

        self.aboutGroup = SettingCardGroup(self.tr('关于'), self)

        self.feedbackCard = PrimaryPushSettingCard(
            self.tr('提供反馈'),
            FIF.FEEDBACK,
            self.tr('提供反馈'),
            self.tr('通过提供反馈帮助我们改进SLE Connect'),
            self.aboutGroup
        )
        self.feedbackCard.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(FEEDBACK_URL)))
        self.aboutCard = PrimaryPushSettingCard(
            self.tr('检查更新'),
            FIF.INFO,
            self.tr('关于'),
            '© ' + self.tr('版权所有') + f" {YEAR}, {AUTHOR}. " +
            self.tr('当前版本') + " " + VERSION,
            self.aboutGroup
        )
        self.aboutCard.button.hide()

        self.aboutGroup.addSettingCard(self.feedbackCard)
        self.aboutGroup.addSettingCard(self.aboutCard)
        self.layout.addWidget(self.aboutGroup, 1, Qt.AlignBottom)

    def com_select_cb(self, obj:OptionsConfigItem):
        self.sle_logger.info('Select COM: ' + self.comboxCard.texts[obj.value])
        self.com_selected = self.comboxCard.texts[obj.value]
    
    def connect_button_clicked(self):
        buttons = self.comboxCard.buttonGroup.buttons()
        index = int(self.com_selected[3:]) - 1
        if buttons[index].isVisible():
            if self.connect_button.text() == '连接':
                self.sle_logger.info('Connect COM: ' + self.com_selected)
                self.sle_entity.start_uart_thread(self.com_selected)
            else:
                self.sle_logger.info('Disconnect COM: ' + self.com_selected)
                self.sle_entity.stop_uart_thread()
        else:
            self.sle_logger.warning('Select COM: ' + self.com_selected + ' is not available!')
            w = MessageBox(
                '警告',
                '请选择有效串口!',
                self
            )
            w.yesButton.setText('好的')
            w.yesButton.setFixedSize(130, 35)
            w.cancelButton.hide()
            if w.exec():
                return

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

class UART_SIGNAL(QThread):
    error_signal = pyqtSignal(str)
    text = ''

    def set_text(self,text):
        self.text = text

    def run(self):
        self.error_signal.emit(self.text)
