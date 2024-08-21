import asyncio
import serial_asyncio
import threading
import time

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
        self.port = None
        self._PC_SN = 1
        self._SLE_SERVER_LIST = []
        self.data = []
        self.writer = None
        self.close_flag = False
        self._connect = False
    
    async def open(self, port, baudrate):
        self.reader, self.writer = await serial_asyncio.open_serial_connection(url=port, baudrate=baudrate)
        self.rec_task = asyncio.create_task(self.read_from_serial(self.reader))
        self.write_task = asyncio.create_task(self.write(self.writer))
        tasks = [self.rec_task, self.write_task]
        done, pending = await asyncio.wait(tasks,return_when="ALL_COMPLETED")
        for task in pending:
            task.cancel()

    def sn_reset(self):
        self._PC_SN = 1

    def sle_hearbeat(self):
        data = bytearray([0xFF, 0xFF, 0x00, 0x08, self._PC_SN, 0x02, 0x00, 0x00, 0x00, 0x00])
        crc = CRC_Check(data, len(data))
        data.append(crc >> 8)
        data.append(crc & 0xFF)
        self.uart_send(data)
        self._PC_SN += 1

    def sle_connect_server(self, addr: list):
        data = bytearray([0xFF, 0xFF, 0x00, 0x0E, self._PC_SN, 0x02, 0x00, 0x01, 0x00, 0x06, addr[0], addr[1], addr[2], addr[3], addr[4], addr[5]])
        crc = CRC_Check(data, len(data))
        data.append(crc >> 8)
        data.append(crc & 0xFF)
        self.uart_send(data)
        self._PC_SN += 1

    def sle_disconnect_server(self, addr: list):
        data = bytearray([0xFF, 0xFF, 0x00, 0x0E, self._PC_SN, 0x02, 0x00, 0x02, 0x00, 0x06, addr[0], addr[1], addr[2], addr[3], addr[4], addr[5]])
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

    def sle_get_device_rssi(self, conn_id: int):
        data = bytearray([0xFF, 0xFF, 0x00, 0x09, self._PC_SN, 0x02, 0x00, 0x04, 0x00, 0x01, conn_id])
        crc = CRC_Check(data, len(data))
        data.append(crc >> 8)
        data.append(crc & 0xFF)
        self.uart_send(data)
        self._PC_SN += 1

    def sle_send_data(self, connid: int, handle: int, type:int, message):
        for i in range(0,len(message),251):
            if i + 251 > len(message):
                msg = message[i:]
            else:
                msg = message[i:i+251]
            data = bytearray([0xFF, 0xFF, 0x00, 0x0C, self._PC_SN, 0x02, 0x00, 0x05, 0x00, 0x00, connid, handle>>8, handle&0xFF, type])
            data[8] = ((len(msg) + 4) >> 8) & 0xFF
            data[9] = (len(msg) + 4) & 0xFF
            for i in msg:
                data.append(i)
            crc = CRC_Check(data, len(data))
            data.append(crc >> 8)
            data.append(crc & 0xFF)
            data[2] = (len(data) - 4) >> 8
            data[3] = (len(data) - 4) & 0xFF
            self.uart_send(data)
            self._PC_SN += 1

    def uart_send(self, data):
        self.data.append(data)

    def uart_cmd_parse(self, cmd, value_len, value):
        data = value.hex()
        if cmd == 0x0000:
            self._connect = True
        elif cmd == 0x0001:
            MAC = data[0:12]
            conn_id = int(data[12:14], 16)
            print(f"连接SLE设备成功，MAC:{MAC},conn_id:{conn_id}")
            for _ in self._SLE_SERVER_LIST:
                if _['MAC'] == MAC:
                    _['conn_id'] = conn_id
                    _['connect'] = True
                    break
            
        elif cmd == 0x0002:
            MAC = data[0:12]
            reason = data[12:14]
            print(f"断开SLE设备连接，MAC:{MAC},原因:{reason}")
            for _ in self._SLE_SERVER_LIST:
                if _['MAC'] == MAC:
                    _['connect'] = False
                    break
        elif cmd == 0x0003:
            Type = int(data[0:2], 16)
            rssi = int(data[2:4], 16)   # RSSI
            if rssi >= 0x80:
                rssi -= 0x100
            MAC = data[4:16]
            data = data[16:]
            print(f"扫描到SLE设备数据类型:{Type},RSSI:{rssi},MAC:{MAC},数据:{data}")
            for _ in self._SLE_SERVER_LIST:
                if _['MAC'] == MAC:
                    _[Type] = data
                    _['RSSI'] = rssi
                    break
            else:
                server_dic = {
                    0x03: None,
                    0x0d: None,
                    "RSSI": rssi,
                    "MAC": MAC,
                    'conn_id': None,
                    'handle': None,
                    'Type': None,
                    'connect': False,
                }
                server_dic[Type] = data
                self._SLE_SERVER_LIST.append(server_dic)
        elif cmd == 0x0004:
            conn_id =  int(data[0:2], 16)
            rssi = int(data[2:4], 16)
            if rssi >= 0x80:
                rssi -= 0x100
            print(f"获取SLE设备RSSI成功，conn_id:{conn_id},RSSI:{rssi}")
            for _ in self._SLE_SERVER_LIST:
                if _['conn_id'] == conn_id:
                    _['RSSI'] = rssi
        elif cmd == 0x0005:
            conn_id = int(data[0:2], 16)
            msg = data[2:]
            print(f"收到SLE设备数据：conn_id:{conn_id},数据：{msg}")
        elif cmd == 0x0006:
            conn_id = int(data[0:2], 16)
            handle = int(data[2:6], 16)
            Type = int(data[6:8], 16)
            print(f"SLE property查找成功，conn_id:{conn_id},handle:{handle},Type:{Type}")
            for _ in self._SLE_SERVER_LIST:
                if _['conn_id'] == conn_id:
                    _['handle'] = handle
                    _['Type'] = Type
                    break

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

    async def read_from_serial(self,reader):
        while True:
            data = await reader.read(1000)
            try:
                self.uart_recv_data_handle(data)
            except Exception as e:
                print(e)
    
    async def write(self, writer):
        while True:
            if len(self.data) > 0:
                print("send data:", self.data[0].hex())
                writer.write(self.data.pop(0))
                await writer.drain()
            await asyncio.sleep(0.2)

    def close(self):
        self.writer.close()
        if self.write_task:
            self.write_task.cancel()
        if self.rec_task:
            self.rec_task.cancel()

def uart_thread(ut:uart,com:str):
    asyncio.run(ut.open(com, 921600))
