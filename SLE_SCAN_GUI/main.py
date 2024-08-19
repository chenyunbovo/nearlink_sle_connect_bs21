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
            threading.Timer(2, self.heartbeat_thread).run()
        else:
            self.stop_uart_thread()

    def sle_scan_done(self):
        self.ut.sle_scan_device(0)

    def sle_start_scan(self):
        self.ut.sle_scan_device(1)
        threading.Timer(15, self.sle_scan_done).run()

    def stop_uart_thread(self):
        self.ut.close()
        if self.ut_thread:
            self.ut_thread.join()
            self.ut_thread = None

    def start_uart_thread(self):
        self.ut_thread = threading.Thread(target=uart_thread, args=(self.ut,'COM7'))
        self.ut_thread.start()
        self.ut.sn_reset()
        # self.ut.sle_hearbeat()
        # threading.Timer(2, self.heartbeat_thread).run()
        self.sle_start_scan()

if __name__ == '__main__':
    m = main()
    m.start_uart_thread()
    while True:
        sleep(1)
