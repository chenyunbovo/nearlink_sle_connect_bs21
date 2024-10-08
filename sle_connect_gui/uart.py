import asyncio
import logging
import serial_asyncio

def CRC_Check(CRC_Ptr, LEN):
    CRC_Value = 0xffff
    for i in range(LEN):
        CRC_Value ^= CRC_Ptr[i]
        for j in range(8):
            if CRC_Value & 0x0001:
                CRC_Value = (CRC_Value >> 1) ^ 0xA001
            else:
                CRC_Value = (CRC_Value >> 1)
    CRC_Value = ((CRC_Value >> 8) + (CRC_Value * 256))
    return CRC_Value & 0xFFFF

class uart:
    def __init__(self, SLE):
        self.sle_logger = logging.getLogger('sle_logger')
        self.port = None
        self._PC_SN = 1
        self._SLE_SERVER_LIST = []
        self.data = []
        self.SLE = SLE
        self.writer = None
        self.close_flag = False
        self._connect = False
        self.__last_data = None
    
    async def open(self, port, baudrate):
        try:
            self.reader, self.writer = await serial_asyncio.open_serial_connection(url=port, baudrate=baudrate)
        except Exception as e:
            self.rec_task = None
            self.write_task = None
            self.SLE.Mainwin.settingInterface.uart_signal.set_text(e.args[0])
            self.SLE.Mainwin.settingInterface.uart_signal.start()
            return
        self.rec_task = asyncio.create_task(self.read_from_serial(self.reader))
        self.write_task = asyncio.create_task(self.write(self.writer))
        tasks = [self.rec_task, self.write_task]
        done, pending = await asyncio.wait(tasks,return_when="ALL_COMPLETED")
        for task in pending:
            task.cancel()

    def sn_reset(self):
        self._PC_SN = 1

    def sle_hearbeat(self):
        data = bytearray([0xFF, 0xFF, 0x00, 0x09, self._PC_SN, 0x02, 0x00, 0x00, 0x00, 0x01, 0x01])
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
            data[2] = (len(data) - 2) >> 8
            data[3] = (len(data) - 2) & 0xFF
            crc = CRC_Check(data, len(data))
            data.append(crc >> 8)
            data.append(crc & 0xFF)
            self.uart_send(data)
            self._PC_SN += 1

    def sle_uart_data_clear(self):
        self.data.clear()

    def uart_send(self, data):
        self.data.append(data)
        self.sle_logger.debug("send data:" + data.hex())

    def __uart_cmd_parse(self, cmd, value_len, value):
        data = value.hex()
        if cmd == 0x0000:
            self._connect = True
        elif cmd == 0x0001:
            MAC = data[0:12]
            conn_id = int(data[12:14], 16)
            self.sle_logger.debug(f"连接SLE设备成功，MAC:{MAC},conn_id:{conn_id}")
            for _ in self._SLE_SERVER_LIST:
                if _['MAC'] == MAC:
                    _['conn_id'] = conn_id
                    _['connect'] = True
                    break
            
        elif cmd == 0x0002:
            MAC = data[0:12]
            reason = data[12:14]
            self.sle_logger.warning(f"断开SLE设备连接，MAC:{MAC},原因:{reason}")
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
            self.sle_logger.debug(f"扫描到SLE设备数据类型:{Type},RSSI:{rssi},MAC:{MAC},数据:{data}")
            for _ in self._SLE_SERVER_LIST:
                if _['MAC'] == MAC:
                    _[Type] = data
                    _['RSSI'] = rssi
                    break
            else:
                server_dic = {
                    0x03: None,
                    0x0b: None,
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
            self.sle_logger.debug(f"获取SLE设备RSSI成功，conn_id:{conn_id},RSSI:{rssi}")
            for _ in self._SLE_SERVER_LIST:
                if _['conn_id'] == conn_id:
                    _['RSSI'] = rssi
        elif cmd == 0x0005:
            conn_id = int(data[0:2], 16)
            msg = data[2:]
            mac = ''
            for _ in self._SLE_SERVER_LIST:
                if _['conn_id'] == conn_id:
                    mac = _['MAC']
                    self.SLE.sle_rec_data_cb(mac, msg)
                    break
            self.sle_logger.debug(f"收到SLE设备数据：mac:{mac},conn_id:{conn_id},数据：{msg}")
        elif cmd == 0x0006:
            conn_id = int(data[0:2], 16)
            handle = int(data[2:6], 16)
            Type = int(data[6:8], 16)
            self.sle_logger.debug(f"SLE property查找成功，conn_id:{conn_id},handle:{handle},Type:{Type}")
            for _ in self._SLE_SERVER_LIST:
                if _['conn_id'] == conn_id:
                    _['handle'] = handle
                    _['Type'] = Type
                    break

    def __uart_recv_data_handle(self, data):
        self.sle_logger.debug("recv data:" + data.hex())
        if self.__last_data != None:
            data = self.__last_data + data
            self.__last_data = None
        index = 0
        while index < len(data):
            if index >= len(data) - 4:
                self.__last_data = data[index:]
                break
            if data[index] == 0xFF and data[index+1] == 0xFF:
                lenth = data[index+2] << 8 | data[index+3]
                if lenth > len(data) - index - 4:
                    self.__last_data = data[index:]
                    break
                crc = data[index + lenth + 2] << 8 | data[index + lenth + 3]
                if crc == CRC_Check(data[index:index + lenth + 2], lenth + 2):
                    flag = data[index+5]
                    if flag == 0x01:
                        i = 6
                        while(i < lenth - 2):
                            cmd = data[index+i] << 8 | data[index+i + 1]
                            value_len = data[index+i + 2] << 8 | data[index+i + 3]
                            self.__uart_cmd_parse(cmd, value_len, data[index+i + 4:index+i + 4 + value_len])
                            i += value_len + 4
                        index += lenth + 4
                    else:
                        self.sle_logger.error("serial data flag error!")
                        index += 1
                else:
                    self.sle_logger.error(f"serial data CRC error!CRC RECV:{crc:04x},CRC CALC:{CRC_Check(data[index:index + lenth + 2], lenth + 2):04x}!")
                    index += 1
            else:
                index += 1
                self.sle_logger.error("serial data head error!")

    async def read_from_serial(self,reader):
        while True:
            data = await reader.read(1000)
            try:
                self.__uart_recv_data_handle(data)
            except Exception as e:
                self.sle_logger.error(e.args[0])
    
    async def write(self, writer):
        while True:
            if len(self.data) > 0:
                writer.write(self.data.pop(0))
                await writer.drain()
            await asyncio.sleep(0.2)

    def close(self):
        if self.write_task:
            self.writer.close()
            self.write_task.cancel()
        if self.rec_task:
            self.rec_task.cancel()

def uart_thread(ut:uart,com:str):
    asyncio.run(ut.open(com, 921600))
