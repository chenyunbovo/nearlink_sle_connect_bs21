/**
 * Copyright (c) @CompanyNameMagicTag 2023-2023. All rights reserved. \n
 *
 * Description: UART Sample Source. \n
 * Author: @CompanyNameTag \n
 * History: \n
 * 2023-06-29, Create file. \n
 */
#include "pinctrl.h"
#include "stdio.h"
#include "uart.h"
#include "hal_uart.h"
#include "osal_debug.h"
#include "cmsis_os2.h"
#include "app_uart.h"
#include "sle_client.h"
#include "soc_osal.h"


static uint8_t g_app_uart_rx_buff[UART_TRANSFER_SIZE] = { 0 };
static uart_buffer_config_t g_app_uart_buffer_config = {
    .rx_buffer = g_app_uart_rx_buff,
    .rx_buffer_size = UART_TRANSFER_SIZE
};
static uint16_t rx_len = 0;

static uint8_t PC_SN = 0;
static uint8_t PICO_SN = 0;

static uint16_t CRC_Check(uint8_t *CRC_Ptr,uint8_t LEN)
{
    uint16_t CRC_Value = 0;
    uint8_t  i = 0;
    uint8_t  j = 0;
    CRC_Value = 0xffff;
    for(i=0;i<LEN;i++)
    {
        CRC_Value ^= *(CRC_Ptr+i);
        for(j=0;j<8;j++)
        {
            if(CRC_Value & 0x00001)
                CRC_Value = (CRC_Value >> 1) ^ 0xA001;
            else
                CRC_Value = (CRC_Value >> 1);
        }
    }
    CRC_Value = ((CRC_Value >> 8) +  (CRC_Value << 8));
    return CRC_Value;
}

void sle_send_heartbeat(void)
{
    uint16_t total_len  = 13;
    uint8_t *send_buff = (uint8_t *)osal_vmalloc(total_len);
    if (send_buff == NULL) {
        osal_printk("uart%d send data malloc fail!\r\n", USER_UART);
        return;
    }
    send_buff[0] = PROTOCOL_HEAD;
    send_buff[1] = PROTOCOL_HEAD;
    send_buff[2] = (total_len - 4) >> 8;
    send_buff[3] = (total_len - 4) & 0xFF;
    send_buff[4] = PC_SN;
    send_buff[5] = PICO_TO_PC_FLAG;
    send_buff[6] = 0x00;
    send_buff[7] = 0x00;
    send_buff[8] = 0x00;
    send_buff[9] = 0x01;
    send_buff[10] = 0x01;
    uint16_t crc = CRC_Check(send_buff, total_len - 2);
    send_buff[total_len - 2] = crc >> 8;
    send_buff[total_len - 1] = crc & 0xFF;
    hal_uart_write(USER_UART, send_buff, total_len);
    PICO_SN++;
    if (send_buff != NULL) {
        osal_vfree(send_buff);
    }
}

void sle_send_scan_data(uint8_t *data, uint16_t len, uint8_t *addr, uint8_t type, uint8_t rssi)
{
    uint16_t total_len = len + 20;
    len = len + 8;
    uint8_t *send_buff = (uint8_t *)osal_vmalloc(total_len);
    if (send_buff == NULL) {
        osal_printk("uart%d send data malloc fail!\r\n", USER_UART);
        return;
    }
    send_buff[0] = PROTOCOL_HEAD;
    send_buff[1] = PROTOCOL_HEAD;
    send_buff[2] = (total_len - 4) >> 8;
    send_buff[3] = (total_len - 4) & 0xFF;
    send_buff[4] = PICO_SN;
    send_buff[5] = PICO_TO_PC_FLAG;
    send_buff[6] = 0x00;
    send_buff[7] = 0x03;
    send_buff[8] = len >> 8;
    send_buff[9] = len & 0xFF;
    send_buff[10] = type;
    send_buff[11] = rssi;
    for (uint16_t i = 0; i < 6; i++) {
        send_buff[12 + i] = addr[i];
    }
    for (uint16_t i = 0; i < len - 8; i++) {
        send_buff[18 + i] = data[i];
    }
    uint16_t crc = CRC_Check(send_buff, total_len - 2);
    send_buff[total_len - 2] = crc >> 8;
    send_buff[total_len - 1] = crc & 0xFF;
    hal_uart_write(USER_UART, send_buff, total_len);
    PICO_SN++;
    if (send_buff != NULL) {
        osal_vfree(send_buff);
    }
}

void sle_send_connect_done(uint8_t *addr, uint8_t conn_id)
{
    uint16_t total_len = 19;
    uint8_t *send_buff = (uint8_t *)osal_vmalloc(total_len);
    if (send_buff == NULL) {
        osal_printk("uart%d send data malloc fail!\r\n", USER_UART);
        return;
    }
    send_buff[0] = PROTOCOL_HEAD;
    send_buff[1] = PROTOCOL_HEAD;
    send_buff[2] = (total_len - 4) >> 8;
    send_buff[3] = (total_len - 4) & 0xFF;
    send_buff[4] = PICO_SN;
    send_buff[5] = PICO_TO_PC_FLAG;
    send_buff[6] = 0x00;
    send_buff[7] = 0x01;
    send_buff[8] = 0x00;
    send_buff[9] = 0x07;
    for (uint16_t i = 0; i < 6; i++) {
        send_buff[10 + i] = addr[i];
    }
    send_buff[16] = conn_id;
    uint16_t crc = CRC_Check(send_buff, total_len - 2);
    send_buff[total_len - 2] = crc >> 8;
    send_buff[total_len - 1] = crc & 0xFF;
    hal_uart_write(USER_UART, send_buff, total_len);
    PICO_SN++;
    if (send_buff != NULL) {
        osal_vfree(send_buff);
    }
}

void sle_send_disconnet_reason(uint8_t *addr, uint8_t dis_res)
{
    uint16_t total_len = 19;
    uint8_t *send_buff = (uint8_t *)osal_vmalloc(total_len);
    if (send_buff == NULL) {
        osal_printk("uart%d send data malloc fail!\r\n", USER_UART);
        return;
    }
    send_buff[0] = PROTOCOL_HEAD;
    send_buff[1] = PROTOCOL_HEAD;
    send_buff[2] = (total_len - 4) >> 8;
    send_buff[3] = (total_len - 4) & 0xFF;
    send_buff[4] = PICO_SN;
    send_buff[5] = PICO_TO_PC_FLAG;
    send_buff[6] = 0x00;
    send_buff[7] = 0x02;
    send_buff[8] = 0x00;
    send_buff[9] = 0x07;
    for (uint16_t i = 0; i < 6; i++) {
        send_buff[10 + i] = addr[i];
    }
    send_buff[16] = dis_res;
    uint16_t crc = CRC_Check(send_buff, 17);
    send_buff[17] = crc >> 8;
    send_buff[18] = crc & 0xFF;
    hal_uart_write(USER_UART, send_buff, total_len);
    PICO_SN++;
    if (send_buff != NULL) {
        osal_vfree(send_buff);
    }
}

void sle_send_rssi_data(uint8_t conn_id, uint8_t rssi)
{
    uint16_t total_len = 14;
    uint8_t *send_buff = (uint8_t *)osal_vmalloc(total_len);
    if (send_buff == NULL) {
        osal_printk("uart%d send data malloc fail!\r\n", USER_UART);
        return;
    }
    send_buff[0] = PROTOCOL_HEAD;
    send_buff[1] = PROTOCOL_HEAD;
    send_buff[2] = (total_len - 4) >> 8;
    send_buff[3] = (total_len - 4) & 0xFF;
    send_buff[4] = PICO_SN;
    send_buff[5] = PICO_TO_PC_FLAG;
    send_buff[6] = 0x00;
    send_buff[7] = 0x04;
    send_buff[8] = 0x00;
    send_buff[9] = 0x02;
    send_buff[10] = conn_id;
    send_buff[11] = rssi;
    uint16_t crc = CRC_Check(send_buff, 12);
    send_buff[12] = crc >> 8;
    send_buff[13] = crc & 0xFF;
    hal_uart_write(USER_UART, send_buff, total_len);
    PICO_SN++;
    if (send_buff != NULL) {
        osal_vfree(send_buff);
    }
}

void sle_send_custom_data(uint8_t conn_id, uint8_t *data, uint16_t len)
{
    uint16_t total_len = len + 13;
    uint8_t *send_buff = (uint8_t *)osal_vmalloc(total_len);
    if (send_buff == NULL) {
        osal_printk("uart%d send data malloc fail!\r\n", USER_UART);
        return;
    }
    send_buff[0] = PROTOCOL_HEAD;
    send_buff[1] = PROTOCOL_HEAD;
    send_buff[2] = (total_len - 4) >> 8;
    send_buff[3] = (total_len - 4) & 0xFF;
    send_buff[4] = PICO_SN;
    send_buff[5] = PICO_TO_PC_FLAG;
    send_buff[6] = 0x00;
    send_buff[7] = 0x05;
    send_buff[8] = (len + 1) >> 8;
    send_buff[9] = (len + 1) & 0xFF;
    send_buff[10] = conn_id;
    for (uint16_t i = 0; i < len; i++) {
        send_buff[11 + i] = data[i];
    }
    uint16_t crc = CRC_Check(send_buff, len + 11);
    send_buff[len + 11] = crc >> 8;
    send_buff[len + 12] = crc & 0xFF;
    hal_uart_write(USER_UART, send_buff, total_len);
    PICO_SN++;
    if (send_buff != NULL) {
        osal_vfree(send_buff);
    }
}

void sle_send_property_data(uint8_t conn_id, uint16_t handle, uint8_t type)
{
    uint16_t total_len = 16;
    uint8_t *send_buff = (uint8_t *)osal_vmalloc(total_len);
    if (send_buff == NULL) {
        osal_printk("uart%d send data malloc fail!\r\n", USER_UART);
        return;
    }
    send_buff[0] = PROTOCOL_HEAD;
    send_buff[1] = PROTOCOL_HEAD;
    send_buff[2] = (total_len - 4) >> 8;
    send_buff[3] = (total_len - 4) & 0xFF;
    send_buff[4] = PICO_SN;
    send_buff[5] = PICO_TO_PC_FLAG;
    send_buff[6] = 0x00;
    send_buff[7] = 0x06;
    send_buff[8] = 0x00;
    send_buff[9] = 0x04;
    send_buff[10] = conn_id;
    send_buff[11] = handle >> 8;
    send_buff[12] = handle & 0xFF;
    send_buff[13] = type;
    uint16_t crc = CRC_Check(send_buff, 14);
    send_buff[14] = crc >> 8;
    send_buff[15] = crc & 0xFF;
    hal_uart_write(USER_UART, send_buff, total_len);
    PICO_SN++;
    if (send_buff != NULL) {
        osal_vfree(send_buff);
    }
}

static void uart_cmd_parse(uint16_t cmd, uint16_t value_len, uint8_t *value)
{
    switch (cmd) {
    case SLE_HEARTBEAT_CMD:
        sle_send_heartbeat();
        break;
    case SLE_CONNECT_CMD:
        sle_client_connect(value);
        break;
    case SLE_DISCONNECT_CMD:
        sle_client_disconnect(value);
        break;
    case SLE_SCAN_CMD:
        if (value[0] == 0x00) {
            sle_stop_scan();
        } else if (value[0] == 0x01) {
            sle_start_scan();
        }
        break;
    case SLE_GET_RSSI_CMD:
        sle_client_get_rssi(value[0]);
        break;
    case SLE_SEND_CMD: {
        uint8_t conn_id = value[0];
        uint16_t handle = (value[1] << 8) | value[2];
        uint8_t type = value[3];
        sle_write(conn_id, handle, type, value + 4, value_len - 4);
        break;
    }
    default:
        osal_printk("uart%d receive data cmd error!\r\n", USER_UART);
        break;
    }
}

static void uart_data_handle(void)
{
    if(rx_len < 8) {
        osal_printk("uart%d receive data total length error!\r\n", USER_UART);
        return;
    }
    if(g_app_uart_rx_buff[0] == PROTOCOL_HEAD && g_app_uart_rx_buff[1] == PROTOCOL_HEAD) {
        uint16_t len = (g_app_uart_rx_buff[2] << 8) | g_app_uart_rx_buff[3];
        uint16_t crc = (g_app_uart_rx_buff[rx_len - 2] << 8) | g_app_uart_rx_buff[rx_len - 1];
        if (len + 4 == rx_len) {
            uint16_t crc_check = CRC_Check(g_app_uart_rx_buff, rx_len - 2);
            if (crc == crc_check) {
                uint8_t flag = g_app_uart_rx_buff[5];
                if (flag == PC_TO_PICO_FLAG) {
                    if(PC_SN != g_app_uart_rx_buff[4]) {
                        PC_SN = g_app_uart_rx_buff[4];
                        for (uint8_t i = 6; i < len - 2;) {
                            uint16_t cmd = (g_app_uart_rx_buff[i] << 8) | g_app_uart_rx_buff[i + 1];
                            uint16_t value_len = (g_app_uart_rx_buff[i + 2] << 8) | g_app_uart_rx_buff[i + 3];
                            printf("uart receive data cmd: 0x%x, value_len:%d\r\n", cmd, value_len);
                            uart_cmd_parse(cmd, value_len, &g_app_uart_rx_buff[i + 4]);
                            i += value_len + 4;
                        }
                    } else {
                        osal_printk("uart%d receive data sn error!\r\n", USER_UART);
                    }
                } else {
                    osal_printk("uart%d receive data flag error!\r\n", USER_UART);
                }
            } else {
                osal_printk("uart%d receive data crc error!\r\n", USER_UART);
                osal_printk("recv crc: 0x%x, crc need: 0x%x\r\n", crc, crc_check);
            }
        } else {
            osal_printk("uart%d receive data len error!\r\n", USER_UART);
        }
    } else {
        osal_printk("uart%d receive data head error!\r\n", USER_UART);
    }
}

static void app_uart_read_int_handler(const void *buffer, uint16_t length, bool error)
{
    unused(error);
    if (buffer == NULL || length == 0) {
        osal_printk("uart%d int mode transfer illegal data!\r\n", USER_UART);
        return;
    }
    uint8_t *buff = (uint8_t *)buffer;
    if (memcpy_s(g_app_uart_rx_buff, length, buff, length) != EOK) {
        osal_printk("uart%d int mode data copy fail!\r\n", USER_UART);
        return;
    }
    printf("uart%d receive data length: %d\r\n", USER_UART, length);
    rx_len = length;
    uart_data_handle();
}

static void app_uart_init_pin(void)
{
    if (USER_UART == 0) {
        uapi_pin_set_mode(UART_TX, HAL_PIO_UART_L0_TXD);
        uapi_pin_set_mode(UART_RX, HAL_PIO_UART_L0_RXD);       
    }else if (USER_UART == 1) {
        uapi_pin_set_mode(UART_TX, HAL_PIO_UART_H0_TXD);
        uapi_pin_set_mode(UART_RX, HAL_PIO_UART_H0_RXD);       
    }else if (USER_UART == 2) {
        uapi_pin_set_mode(UART_TX, HAL_PIO_UART_L1_TXD);
        uapi_pin_set_mode(UART_RX, HAL_PIO_UART_L1_RXD);       
    }
}

static void app_uart_init_config(void)
{
    uart_attr_t attr = {
        .baud_rate = UART_BAUDRATE,
        .data_bits = UART_DATA_BIT_8,
        .stop_bits = UART_STOP_BIT_1,
        .parity = UART_PARITY_NONE
    };

    uart_pin_config_t pin_config = {
        .tx_pin = UART_TX,
        .rx_pin = UART_RX,
        .cts_pin = PIN_NONE,
        .rts_pin = PIN_NONE
    };
    uapi_uart_init(USER_UART, &pin_config, &attr, NULL, &g_app_uart_buffer_config);
}

void uart_task_init(void)
{
    app_uart_init_pin();
    app_uart_init_config();
    osal_printk("uart%d int mode register receive callback start!\r\n", USER_UART);
    if (uapi_uart_register_rx_callback(USER_UART, UART_RX_CONDITION_FULL_OR_SUFFICIENT_DATA_OR_IDLE,
                                       1, app_uart_read_int_handler) == ERRCODE_SUCC) {
        osal_printk("uart%d int mode register receive callback succ!\r\n", USER_UART);
    }
}
