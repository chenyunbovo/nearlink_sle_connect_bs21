import threading
from uart import uart

if __name__ == "__main__":
    ser = uart()
    ser.open("com7", 115200)
    ser.sle_scan_device(0x01)
    ser.uart_recv_threading()
