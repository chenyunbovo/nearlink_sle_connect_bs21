import threading
from uart import uart, uart_thread
import serial
import serial.tools.list_ports
import inspect
import ctypes
from time import sleep

class main:
    def __init__(self):
        self.ut = uart()
        
    def stop_uart_thread(self):
        self.ut.close()
        print("stop uart thread")
        self.thread.join()
        print("thread joined")

    def start_uart_thread(self):
        self.thread = threading.Thread(target=uart_thread, args=(self.ut,'COM30'))
        self.thread.start()

def kill_thread(ident):
    try:
        tid = ident
        if not inspect.isclass(SystemExit):
            raise TypeError("Only types can be raised (not instances)")
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid), ctypes.py_object(SystemExit))
        if res == 0:
            print("invalid thread id")
        elif res != 1:
            # """if it returns a number greater than one, you're in trouble,
            # and you should call it again with exc=NULL to revert the effect"""
            ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
            raise SystemError("PyThreadState_SetAsyncExc failed")
    except Exception as e:
        print(e)

if __name__ == '__main__':
    m = main()
    m.start_uart_thread()
    sleep(2)
    m.stop_uart_thread()
    m.start_uart_thread()
    sleep(3)
    m.stop_uart_thread()