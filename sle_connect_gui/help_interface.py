from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHBoxLayout, QFrame

from qfluentwidgets import (SubtitleLabel, setFont)

class HelpWidget(QFrame):
    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.label = SubtitleLabel('帮助界面', self)
        self.hBoxLayout = QHBoxLayout(self)

        setFont(self.label, 24)
        self.label.setAlignment(Qt.AlignCenter)
        self.hBoxLayout.addWidget(self.label, 0, Qt.AlignCenter)
        self.setObjectName(text.replace(' ', '-'))