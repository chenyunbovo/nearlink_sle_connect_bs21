#ifndef APP_UART_H
#define APP_UART_H

#define USER_UART                          2
#define UART_RX                            23
#define UART_TX                            24
#define UART_BAUDRATE                      921600
#define UART_TRANSFER_SIZE                 256

#define PROTOCOL_HEAD                      0xFF

#define PICO_TO_PC_FLAG                    0x01
#define PC_TO_PICO_FLAG                    0x02

typedef enum
{
    SLE_HEARTBEAT_CMD = 0x0000,
    SLE_CONNECT_CMD = 0x0001,
    SLE_DISCONNECT_CMD = 0x0002,
    SLE_SCAN_CMD = 0x0003,
    SLE_GET_RSSI_CMD = 0x0004,
    SLE_SEND_CMD = 0x0005,
    SLE_PROPERTY_CMD = 0x0006,
} uart_cmd_t;

void uart_task_init(void);
void sle_send_heartbeat(void);
void sle_send_scan_data(uint8_t *data, uint16_t len, uint8_t *addr, uint8_t type, uint8_t rssi);
void sle_send_connect_done(uint8_t *addr, uint8_t conn_id);
void sle_send_disconnet_reason(uint8_t *addr, uint8_t dis_res);
void sle_send_rssi_data(uint8_t conn_id, uint8_t rssi);
void sle_send_custom_data(uint8_t conn_id, uint8_t *data, uint16_t len);
void sle_send_property_data(uint8_t conn_id, uint16_t handle, uint8_t type);

#endif // APP_UART_H
