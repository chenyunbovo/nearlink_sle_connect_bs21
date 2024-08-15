#include "common_def.h"
#include "osal_debug.h"
#include "cmsis_os2.h"
#include "app_init.h"
#include "pm_clock.h"
#include "boards.h"
#include "pinctrl.h"
#include "gpio.h"
#include "hal_gpio.h"
#include "app_uart.h"
#include "sle_client.h"

static void *sys_run_led_task(const char *arg)
{
    unused(arg);
    while (1) {
        uapi_gpio_toggle(PIN_MODE_31);
        osDelay(500);
    }
    return NULL;
}

static void led_task_init(void)
{
    osThreadAttr_t attr;

    attr.name = "TasksTask";
    attr.attr_bits = 0U;
    attr.cb_mem = NULL;
    attr.cb_size = 0U;
    attr.stack_mem = NULL;
    attr.stack_size = 1024;
    attr.priority = 17;
    uapi_pin_set_mode(PIN_MODE_31, HAL_PIO_FUNC_GPIO);
    uapi_gpio_set_dir(PIN_MODE_31, GPIO_DIRECTION_OUTPUT);
    uapi_gpio_set_val(PIN_MODE_31, GPIO_LEVEL_LOW);
    if (osThreadNew((osThreadFunc_t)sys_run_led_task, NULL, &attr) == NULL) {
        printf("[app_main] Falied to create sys_run_led_task!\n");
    }
}

static void app_main(void)
{
    if (uapi_clock_control(CLOCK_CONTROL_FREQ_LEVEL_CONFIG, CLOCK_FREQ_LEVEL_HIGH) == ERRCODE_SUCC) {
        osal_printk("Clock config succ.\r\n");
    } else {
        osal_printk("Clock config fail.\r\n");
    }
    osal_printk("SLE CLIENT APP START.\r\n");
    led_task_init();
    uart_task_init();
    app_sle_client_init();
}

app_run(app_main);
