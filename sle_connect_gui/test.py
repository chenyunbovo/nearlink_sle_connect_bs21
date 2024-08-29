from PyQt5.QtWidgets import QApplication, QTextEdit, QWidget, QVBoxLayout
from PyQt5.QtGui import QTextCharFormat, QColor, QTextCursor
import sys

class TextEditDemo(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('TextEdit 设置文本颜色示例')
        self.resize(300, 200)

        # 创建 QTextEdit
        self.textEdit = QTextEdit(self)
        layout = QVBoxLayout()
        layout.addWidget(self.textEdit)
        self.setLayout(layout)

        # 改变文本颜色
        self.changeTextColor('这是红色文本', QColor(255, 0, 0))

    def changeTextColor(self, text, color):
        # 获取 QTextEdit 的 QTextCursor
        cursor = self.textEdit.textCursor()
        
        # 创建 QTextCharFormat 并设置颜色
        textFormat = QTextCharFormat()
        textFormat.setForeground(color)
        
        # 应用格式
        cursor.mergeCharFormat(textFormat)
        
        # 添加文本
        cursor.insertText(text)
        
        # 重置格式以便后续文本使用默认格式
        textFormat.setForeground(QColor(0, 0, 0))
        cursor.mergeCharFormat(textFormat)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    demo = TextEditDemo()
    demo.show()
    sys.exit(app.exec_())