import threading
import time
# 定义回调函数
def timer_callback():
    e = time.time()
    print(e-s)  
    print("定时器触发！")


# 创建一个定时器，10秒后触发

timer = threading.Timer(10.0, timer_callback)
s = time.time()
# 启动定时器
timer.start()
