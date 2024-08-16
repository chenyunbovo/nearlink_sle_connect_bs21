import serial
import serial.tools.list_ports
from time import sleep
import asyncio
import serial_asyncio
import time
import threading

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
        self.data = []
    
    async def open(self, port, baudrate):
        self.reader, self.writer = await serial_asyncio.open_serial_connection(url=port, baudrate=baudrate)
        rec_task = asyncio.create_task(self.read_from_serial(self.reader))
        write_task = asyncio.create_task(self.write(self.writer))
        await rec_task
        await write_task

    async def read_from_serial(self,reader):
        while True:
            data = await reader.read(1000)
            try:
                # self.uart_recv_data_handle(data)
                print("recv data:", data)
            except Exception as e:
                print(e)

    def sle_connect_server(self, addr: list):
        data = bytearray([0xFF, 0xFF, 0x00, 0x0E, self._PC_SN, 0x02, 0x00, 0x01, 0x00, 0x06, addr[0], addr[1], addr[2], addr[3], addr[4], addr[5]])
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
        self.data.append(data)

    async def write(self, writer):
        while True:
            if len(self.data) > 0:
                writer.write(self.data.pop(0))
                await writer.drain()
            await asyncio.sleep(0.1)
    
    def uart_cmd_parse(self, cmd, value_len, value):
        if cmd == 0x0003:
            data = value.hex()
            Type = data[0:2]
            rssi = int(data[2:4], 16)   # RSSI
            if rssi >= 0x80:
                rssi -= 0x100
            MAC = data[4:16]
            data = data[16:]
            print(f"扫描到SLE设备数据类型:{Type},RSSI:{rssi},MAC:{MAC}")
            print("扫描到SLE设备数据：", data)
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


def main_thread():

    asyncio.run(ut.open("com30", 115200))

if __name__ == '__main__':
    ut = uart()
    thread = threading.Thread(target=main_thread)
    thread.start()
    ut.sle_scan_device(0x01)
    for i in range(10):
        ut.sle_connect_server([0x00, 0x00, 0x00, 0x00, 0x00, 0x00])