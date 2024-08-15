import serial
import serial.tools.list_ports
from time import sleep

def CRC_Check(CRC_Ptr, LEN):
    CRC_Value = 0xffff
    for i in range(LEN):
        CRC_Value ^= CRC_Ptr[i]
        for j in range(8):
            if CRC_Value & 0x0001:
                CRC_Value = (CRC_Value >> 1) ^ 0xA001
            else:
                CRC_Value = (CRC_Value >> 1)
            # print("CRC_Value:0x%04X" %CRC_Value)
    CRC_Value = ((CRC_Value >> 8) + (CRC_Value * 256))
    return CRC_Value & 0xFFFF

class uart:
    def __init__(self):
        self.ser = None
        self.port = None
        self.baudrate = None
        self._PC_SN = 1
        self._SLE_SERVER_LIST = []
    
    def open(self, port, baudrate):
        self.port = port
        self.baudrate = baudrate
        self.ser = serial.Serial(port, baudrate)
        if self.ser.isOpen():
            print("open serial success")
            return True
        else:
            print("open serial failed")
            return False

    def uart_recv_threading(self):
        while True:
            data = self.ser.read_all()
            if data!=b'':
                try:
                    self.uart_recv_data_handle(data)
                except Exception as e:
                    print(e)
            self.ser.flushInput()
            sleep(0.09)

    def sle_connect_server(self, addr: list):
        data = bytearray([0xFF, 0xFF, 0x00, 0x0E, self._PC_SN, 0x02, 0x00, 0x01, 0x00, 0x06, addr[0], addr[1], addr[2], addr[3], addr[4], addr[5]])
        print(len(data)-4)
        crc = CRC_Check(data, len(data))
        data.append(crc >> 8)
        data.append(crc & 0xFF)
        self.uart_send(data)
        self._PC_SN += 1

    def sle_disconnect_server(self):
        data = bytearray([0xFF, 0xFF, 0x00, 0x09, self._PC_SN, 0x02, 0x00, 0x02, 0x00, 0x01, 0x01])
        crc = CRC_Check(data, len(data))
        data.append(crc >> 8)
        data.append(crc & 0xFF)
        self.uart_send(data)
        self._PC_SN += 1

    def sle_scan_device(self, action: int):
        data = bytearray([0xFF, 0xFF, 0x00, 0x09, self._PC_SN, 0x02, 0x00, 0x03, 0x00, 0x01, action])
        crc = CRC_Check(data, len(data))
        data.append(crc >> 8)
        data.append(crc & 0xFF)
        self.uart_send(data)
        self._PC_SN += 1

    def sle_get_device_rssi(self):
        data = bytearray([0xFF, 0xFF, 0x00, 0x09, self._PC_SN, 0x02, 0x00, 0x04, 0x00, 0x01, 0x01])
        crc = CRC_Check(data, len(data))
        data.append(crc >> 8)
        data.append(crc & 0xFF)
        self.uart_send(data)
        self._PC_SN += 1

    def sle_send_data(self, msg: list):
        data = bytearray([0xFF, 0xFF, 0x00, 0x0C, self._PC_SN, 0x02, 0x00, 0x05, 0x00, 0x00])
        data[3] = (len(data) - 4) >> 8
        data[4] = (len(data) - 4) & 0xFF
        data[8] = (len(msg) >> 8) & 0xFF
        data[9] = len(msg) & 0xFF
        for i in msg:
            data.append(i)
        crc = CRC_Check(data, len(data))
        data.append(crc >> 8)
        data.append(crc & 0xFF)
        self.uart_send(data)
        self._PC_SN += 1

    def uart_send(self, data):
        print("send data:", data.hex())
        self.ser.write(data)
    
    def uart_cmd_parse(self, cmd, value_len, value):
        if cmd == 0x0003:
            data = value.hex()
            Type = data[0:2]
            rssi = int(data[2:4], 16)   # RSSI
            if rssi >= 0x80:  # 检查最高位是否为1
                rssi -= 0x100  # 转换为有符号数
            print(f"扫描到SLE设备数据类型:{Type},RSSI:{rssi},MAC:{data[4:16]}")
            print("扫描到SLE设备数据：", data[16:])
        elif cmd == 0x0004:
            print("对端设备RSSI：", value)
        elif cmd == 0x0005:
            print("收到SERVER数据：", value)

    def uart_recv_data_handle(self, data):
        print("recv data:", data.hex())
        index = 0
        while index < len(data) - 8:
            print("index:", index)
            if data[index] == 0xFF and data[index+1] == 0xFF:
                lenth = data[index+2] << 8 | data[index+3]
                crc = data[index + lenth + 2] << 8 | data[index + lenth + 3]
                if crc == CRC_Check(data[index:index + lenth + 2], lenth + 2):
                    flag = data[index+5]
                    if flag == 0x01:
                        i = 6
                        while(i < lenth - 2):
                            cmd = data[index+i] << 8 | data[index+i + 1]
                            value_len = data[index+i + 2] << 8 | data[index+i + 3]
                            self.uart_cmd_parse(cmd, value_len, data[index+i + 4:index+i + 4 + value_len])
                            i += value_len + 4
                        index += lenth + 4
                    else:
                        print("serial data flag error!")
                        index += 1
                else:
                    print(f"CRC RECV:{crc:04x}")
                    print(f"CRC CALC:{CRC_Check(data[index:index + lenth + 2], lenth + 2):04x}")
                    print("serial data CRC error!")
                    index += 1
            else:
                index += 1
                print("serial data head error!")

if __name__ == "__main__":
    ser = uart()
    ser.open("com7", 115200)
    ser.sle_scan_device(0x01)
    ser.uart_recv_threading()
    # FF FF 00 14 DE 01 00 03 00 0C 11 22 33 44 55 66 01 02 01 02 02 00 19 43
    # data = bytearray([0xFF, 0xFF, 0x00, 0x14, 0xDE, 0x01, 0x00, 0x03, 0x00, 0x0C, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x01, 0x02, 0x01, 0x02, 0x02, 0x00])
    # print("%04X" %CRC_Check(data, len(data)))
