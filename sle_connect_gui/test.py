from PyQt5.QtCore import QThread, pyqtSignal
from qfluentwidgets import FluentWindow
import sys
from time import sleep
import os
from PyQt5.QtWidgets import QApplication

class ExampleThread(QThread):
    # 定义一个信号
    exampleSignal = pyqtSignal(str)

    def run(self):
        # 这里是线程的工作内容
        # 假设我们要在这里执行一些耗时的任务
        # 并且在任务完成后发出信号
        while True:
            sleep(1)
            self.exampleSignal.emit("任务完成")

# 在你的主窗口或其他地方使用这个线程
class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        # 创建线程实例
        self.exampleThread = ExampleThread()
        # 连接信号
        self.exampleThread.exampleSignal.connect(self.handleSignal)
        # 启动线程
        self.exampleThread.start()

    def handleSignal(self, message):
        # 处理线程发出的信号
        print(message)

# 运行主窗口
app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec_())