#include "common_def.h"
#include "stdio.h"
#include "soc_osal.h"
#include "app_init.h"
#include "uart.h"
#include "pm_clock.h"
#include "sle_low_latency.h"
#include "sle_connection_manager.h"
#include "sle_ssap_client.h"
#include "securec.h"
#include "product.h"
#include "bts_le_gap.h"
#include "bts_device_manager.h"
#include "sle_device_manager.h"
#include "sle_device_discovery.h"
#include "app_uart.h"
#include "sle_client.h"

#define UUID_16BIT_LEN                  2
#define UUID_128BIT_LEN                 16
#define SLE_TASK_DELAY_MS          1000
#define SLE_WAIT_SLE_CORE_READY_MS 5000
#define SLE_RECV_CNT               1000
#define SLE_LOW_LATENCY_2K         2000
#ifndef SLE_SERVER_NAME
#define SLE_SERVER_NAME            "sle_uart_server"
#endif
#define SLE_CLIENT_LOG             "[sle client]"

static sle_dev_manager_callbacks_t g_sle_dev_mgr_cbk = { 0 };
static sle_announce_seek_callbacks_t g_sle_seek_cbk = { 0 };
static sle_connection_callbacks_t g_sle_connect_cbk = { 0 };
static ssapc_callbacks_t g_sle_ssapc_cbk = { 0 };
static sle_addr_t g_sle_remote_addr = { 0 };

void sle_client_init(ssapc_notification_callback notification_cb, ssapc_indication_callback indication_cb);
void sle_notification_cb(uint8_t client_id, uint16_t conn_id, ssapc_handle_value_t *data,errcode_t status);
void sle_indication_cb(uint8_t client_id, uint16_t conn_id, ssapc_handle_value_t *data,errcode_t status);

void sle_write( uint8_t conn_id, uint16_t handle, uint8_t type, uint8_t *data, uint16_t len)
{
    ssapc_write_param_t sle_send_param;
    sle_send_param.handle = handle;
    sle_send_param.type = type;
    sle_send_param.data_len = len;
    sle_send_param.data = (uint8_t *)data;
    ssapc_write_req(0, conn_id, &sle_send_param);
}

void sle_start_scan(void)
{
    sle_seek_param_t param = { 0 };
    param.own_addr_type = 0;
    param.filter_duplicates = 0;
    param.seek_filter_policy = 0;
    param.seek_phys = 1;
    param.seek_type[0] = 1;
    param.seek_interval[0] = 8000;
    param.seek_window[0] = 100;
    sle_set_seek_param(&param);
    sle_start_seek();
}

void sle_stop_scan(void)
{
    sle_stop_seek();
}

void sle_client_disconnect(uint8_t *addr)
{
    memcpy_s(g_sle_remote_addr.addr, sizeof(g_sle_remote_addr.addr), addr, 6);
    sle_disconnect_remote_device(&g_sle_remote_addr);
}

void sle_client_connect(uint8_t *addr)
{
    memcpy_s(g_sle_remote_addr.addr, sizeof(g_sle_remote_addr.addr), addr, 6);
    sle_connect_remote_device(&g_sle_remote_addr);
}

void sle_client_get_rssi(uint8_t conn_id)
{
    sle_read_remote_device_rssi(conn_id);
}

static void sle_client_sle_power_on_cbk(uint8_t status)          // sle客户端上电回调
{
    osal_printk("sle power on: %d.\r\n", status);
    enable_sle();
}

static void sle_client_sle_enable_cbk(uint8_t status)            // sle客户端使能回调
{
    osal_printk("sle enable: %d.\r\n", status);
    sle_client_init(sle_notification_cb, sle_indication_cb);
}

static void sle_client_seek_enable_cbk(errcode_t status)         // sle客户端搜索使能回调
{
    if (status != 0) {
        osal_printk("%s sle_client_seek_enable_cbk,status error\r\n", SLE_CLIENT_LOG);
    }
}

static void sle_client_seek_result_info_cbk(sle_seek_result_info_t *seek_result_data)        // sle客户端搜索结果回调
{
    if (seek_result_data == NULL) {
        osal_printk("status error\r\n");
    } else {
        sle_send_scan_data(seek_result_data->data, seek_result_data->data_length, seek_result_data->addr.addr, seek_result_data->event_type, seek_result_data->rssi);
    }
}

static void sle_client_seek_disable_cbk(errcode_t status)            // sle客户端搜索去使能回调
{
    if (status != 0) {
        osal_printk("%s sle_client_seek_disable_cbk,status error = %x\r\n", SLE_CLIENT_LOG, status);
    }
}

static void sle_client_connect_state_changed_cbk(uint16_t conn_id, const sle_addr_t *addr,
                                                             sle_acb_state_t conn_state, sle_pair_state_t pair_state,
                                                             sle_disc_reason_t disc_reason)         // sle客户端连接状态改变回调
{
    unused(pair_state);
    unused(conn_id);
    switch (conn_state) {
    case SLE_ACB_STATE_CONNECTED:
        osal_printk("%s SLE_ACB_STATE_CONNECTED\r\n", SLE_CLIENT_LOG);
        sle_send_connect_done((uint8_t *)addr->addr, conn_id);
        if (pair_state == SLE_PAIR_NONE) {
            memcpy_s(g_sle_remote_addr.addr, sizeof(g_sle_remote_addr.addr), addr->addr, 6);
            sle_pair_remote_device(&g_sle_remote_addr);
        }
        break;
    case SLE_ACB_STATE_NONE:
        osal_printk("%s SLE_ACB_STATE_NONE\r\n", SLE_CLIENT_LOG);
        break;
    case SLE_ACB_STATE_DISCONNECTED:
        osal_printk("%s SLE_ACB_STATE_DISCONNECTED\r\n", SLE_CLIENT_LOG);
        sle_send_disconnet_reason((uint8_t *)addr->addr, disc_reason);
        memcpy_s(g_sle_remote_addr.addr, sizeof(g_sle_remote_addr.addr), addr->addr, 6);
        sle_remove_paired_remote_device(&g_sle_remote_addr);
        break;
    default:
        osal_printk("%s status error\r\n", SLE_CLIENT_LOG);
        break;
    }
}

void  sle_client_pair_complete_cbk(uint16_t conn_id, const sle_addr_t *addr, errcode_t status)   // sle客户端配对完成回调
{
    osal_printk("%s pair complete conn_id:%d, addr:%02x***%02x%02x\n", SLE_CLIENT_LOG, conn_id,
                addr->addr[0], addr->addr[4], addr->addr[5]);
    if (status == ERRCODE_SUCC) {
        ssap_exchange_info_t info = {0};
        info.mtu_size = 251;
        info.version = 1;
        ssapc_exchange_info_req(0, conn_id, &info);
    }
}


static void sle_client_exchange_info_cbk(uint8_t client_id, uint16_t conn_id, ssap_exchange_info_t *param, errcode_t status)        // sle客户端交换信息回调        
{
    osal_printk("%s exchange_info_cbk,pair complete client id:%d status:%d\r\n",
                SLE_CLIENT_LOG, client_id, status);
    osal_printk("%s exchange mtu, mtu size: %d, version: %d.\r\n", SLE_CLIENT_LOG,
                param->mtu_size, param->version);
    ssapc_find_structure_param_t find_param = { 0 };
    find_param.type = SSAP_FIND_TYPE_PROPERTY;
    find_param.start_hdl = 1;
    find_param.end_hdl = 0xFFFF;
    ssapc_find_structure(0, conn_id, &find_param);
}

static void sle_client_find_structure_cbk(uint8_t client_id, uint16_t conn_id, ssapc_find_service_result_t *service, errcode_t status)                 // sle客户端查找结构回调
{
    osal_printk("%s find structure cbk client: %d conn_id:%d status: %d \r\n", SLE_CLIENT_LOG,
                client_id, conn_id, status);
    osal_printk("%s find structure start_hdl:[0x%02x], end_hdl:[0x%02x], uuid len:%d\r\n", SLE_CLIENT_LOG,
                service->start_hdl, service->end_hdl, service->uuid.len);
}

static void sle_client_find_property_cbk(uint8_t client_id, uint16_t conn_id, ssapc_find_property_result_t *property, errcode_t status)          // sle客户端查找属性回调
{
    osal_printk("%s sle_client_find_property_cbk, client id: %d, conn id: %d, operate ind: %d, "
                "descriptors count: %d status:%d property->handle %d\r\n", SLE_CLIENT_LOG,
                client_id, conn_id, property->operate_indication,
                property->descriptors_count, status, property->handle);
    sle_send_property_data(conn_id, property->handle, SSAP_PROPERTY_TYPE_VALUE);
}

static void sle_client_find_structure_cmp_cbk(uint8_t client_id, uint16_t conn_id,
                                                          ssapc_find_structure_result_t *structure_result,
                                                          errcode_t status)                                         // sle客户端查找结构比较回调
{
    unused(conn_id);
    osal_printk("%s sle_client_find_structure_cmp_cbk,client id:%d status:%d type:%d uuid len:%d \r\n",
                SLE_CLIENT_LOG, client_id, status, structure_result->type, structure_result->uuid.len);
}

static void sle_client_write_cfm_cb(uint8_t client_id, uint16_t conn_id, ssapc_write_result_t *write_result, errcode_t status)           // sle客户端写确认回调
{
    osal_printk("%s sle_client_write_cfm_cb, conn_id:%d client id:%d status:%d handle:%02x type:%02x\r\n",
                SLE_CLIENT_LOG, conn_id, client_id, status, write_result->handle, write_result->type);
}

void sle_notification_cb(uint8_t client_id, uint16_t conn_id, ssapc_handle_value_t *data,errcode_t status)  // sle客户端通知回调
{
    unused(client_id);
    unused(status);
    osal_printk("sle client recived notify data : %.*s\r\n",data->data_len, data->data);
    sle_send_custom_data(conn_id, data->data, data->data_len);
}

void sle_indication_cb(uint8_t client_id, uint16_t conn_id, ssapc_handle_value_t *data,errcode_t status)    // sle客户端指示回调
{
    unused(client_id);
    unused(status);
    osal_printk("sle client recived indication data : %s\r\n", data->data);
    sle_send_custom_data(conn_id, data->data, data->data_len);
}

void sle_read_rssi_cb(uint16_t conn_id, int8_t rssi, errcode_t status)    // sle客户端读取RSSI回调
{
    osal_printk("%s sle_read_rssi_cb, conn_id:%d, rssi:%d, status:%d\r\n", SLE_CLIENT_LOG, conn_id, rssi, status);
    sle_send_rssi_data(conn_id, rssi);
}

static void sle_client_connect_cbk_register(void)
{
    g_sle_connect_cbk.connect_state_changed_cb = sle_client_connect_state_changed_cbk;
    g_sle_connect_cbk.pair_complete_cb =  sle_client_pair_complete_cbk;
    g_sle_connect_cbk.read_rssi_cb = sle_read_rssi_cb;
    sle_connection_register_callbacks(&g_sle_connect_cbk);
}

static void sle_client_ssapc_cbk_register(ssapc_notification_callback notification_cb,ssapc_notification_callback indication_cb)
{
    g_sle_ssapc_cbk.exchange_info_cb = sle_client_exchange_info_cbk;
    g_sle_ssapc_cbk.find_structure_cb = sle_client_find_structure_cbk;
    g_sle_ssapc_cbk.ssapc_find_property_cbk = sle_client_find_property_cbk;
    g_sle_ssapc_cbk.find_structure_cmp_cb = sle_client_find_structure_cmp_cbk;
    g_sle_ssapc_cbk.write_cfm_cb = sle_client_write_cfm_cb;
    g_sle_ssapc_cbk.notification_cb = notification_cb;
    g_sle_ssapc_cbk.indication_cb = indication_cb;
    ssapc_register_callbacks(&g_sle_ssapc_cbk);
}

static void sle_client_seek_cbk_register(void)
{
    g_sle_seek_cbk.seek_enable_cb = sle_client_seek_enable_cbk;
    g_sle_seek_cbk.seek_result_cb = sle_client_seek_result_info_cbk;
    g_sle_seek_cbk.seek_disable_cb = sle_client_seek_disable_cbk;
    sle_announce_seek_register_callbacks(&g_sle_seek_cbk);
}

void sle_client_init(ssapc_notification_callback notification_cb, ssapc_indication_callback indication_cb)
{
    sle_client_seek_cbk_register();
    sle_client_connect_cbk_register();
    sle_client_ssapc_cbk_register(notification_cb, indication_cb);
}

void sle_client_dev_cbk_register(void)
{
    g_sle_dev_mgr_cbk.sle_power_on_cb = sle_client_sle_power_on_cbk;
    g_sle_dev_mgr_cbk.sle_enable_cb = sle_client_sle_enable_cbk;
    sle_dev_manager_register_callbacks(&g_sle_dev_mgr_cbk);
    enable_sle();
}

void app_sle_client_init(void)
{
    osal_kthread_lock();
    sle_client_dev_cbk_register();
    osal_kthread_unlock();
}
