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
        self.ut_thread = None

    def heartbeat_thread(self):
        if self.ut._connect:
            self.ut.sle_hearbeat()
            self.ut._connect = False
            threading.Timer(5, self.heartbeat_thread).run()
        else:
            self.stop_uart_thread()
            

    def stop_uart_thread(self):
        self.ut.close()
        if self.ut_thread:
            self.ut_thread.join()
            self.ut_thread = None

    def start_uart_thread(self):
        self.ut_thread = threading.Thread(target=uart_thread, args=(self.ut,'COM30'))
        self.ut_thread.start()
        self.ut.sn_reset()
        self.ut.sle_hearbeat()
        threading.Timer(5, self.heartbeat_thread).run()

if __name__ == '__main__':
    m = main()
    m.start_uart_thread()
    sleep(5)
    m.stop_uart_thread()
    m.start_uart_thread()
    sleep(5)
    m.stop_uart_thread()