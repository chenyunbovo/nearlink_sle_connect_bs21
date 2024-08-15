#ifndef APP_SLE_CLIENT_H
#define APP_SLE_CLIENT_H
#include "stdint.h"

void sle_write(uint8_t *data, uint16_t len);
void app_sle_client_init(void);

// 扫描函数
void sle_start_scan(void);

// 停止扫描函数
void sle_stop_scan(void);

// 连接函数
void sle_client_connect(uint8_t *addr);

// 断开连接函数
void sle_client_disconnect(void);

// 获取已连接设备的RSSI
void sle_client_get_rssi(void);

#endif // APP_SLE_CLIENT_H
