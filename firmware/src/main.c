/*
 * main.c - init order and the control loop.
 *
 * Control loop duties:
 *   - every 100 ms (10 Hz): read TMP117, run the HV temperature-
 *     compensation update at exactly that rate (hv_ctrl's slew math
 *     assumes 10 Hz), sample the ADN2813 LOS pin, publish the
 *     environment into usb_app's status, blink the status LED slowly.
 *   - every iteration: poll the USB device layer for a command frame
 *     and answer it through usb_app; forward any ready capture buffer
 *     to the host, and through the BER checker while a test runs.
 *
 * The USB device layer is the stub (usb_device_stub.c), so the poll
 * below currently receives USB_DEV_NOT_IMPLEMENTED every time and the
 * loop simply carries on - that is deliberate: the control/safety
 * duties above must not depend on USB working.
 */
#include "adn2813.h"
#include "board.h"
#include "capture.h"
#include "clocks.h"
#include "dac8562.h"
#include "gpio.h"
#include "hv_ctrl.h"
#include "i2c.h"
#include "spi.h"
#include "tmp117.h"
#include "usb_app.h"
#include "usb_device_if.h"

static hv_ctrl_t g_hv;
static capture_t g_cap;
static usb_app_t g_app;

int main(void)
{
    uint32_t last_10hz = 0;
    float temp_c = 0.0f;
    int temp_valid = 0;
    int sensor_ok;

    /* Init order matters: clocks -> pin/peripheral clocks -> GPIO ->
     * buses -> devices -> control -> capture -> USB(app + device). */
    (void)clocks_init(); /* on failure we continue at the reset clock:
                            the LED/status paths still work, and a
                            clock fault is visible by the slow LED */
    board_enable_peripheral_clocks();
    gpio_init_board_pins();
    i2c_init();
    spi_init();

    (void)dac8562_init();
    sensor_ok = (tmp117_init() == 0);
    (void)adn2813_init(); /* absent CDR must not block the rest */
    hv_ctrl_init(&g_hv);
    capture_init(&g_cap);
    usb_app_init(&g_app, &g_hv, &g_cap);
    (void)usb_dev_init(); /* stub: returns USB_DEV_NOT_IMPLEMENTED */

    for (;;) {
        uint32_t now = board_millis();

        if (now - last_10hz >= 100u) {
            int los;
            last_10hz = now;
            if (sensor_ok &&
                tmp117_read_c(&temp_c) == 0) {
                temp_valid = 1;
            } else {
                temp_valid = 0;
            }
            (void)hv_ctrl_update(&g_hv, temp_c, temp_valid);
            los = adn2813_los_asserted();
            usb_app_set_environment(&g_app, temp_c, temp_valid,
                                    los > 0 ? 1 : 0);
            /* Slow heartbeat: one toggle per 100 ms step gives a
             * visible ~0.5 Hz blink (with SysTick actually running). */
            gpio_write(BOARD_LED_PORT, BOARD_LED_PIN,
                       (now / 500u) & 1u);
        }

        {
            uint8_t cmd[64];
            uint8_t resp[64];
            int n = usb_dev_recv(cmd, sizeof cmd);
            if (n > 0) {
                size_t rlen = usb_app_process(&g_app, cmd, (size_t)n,
                                              resp, sizeof resp);
                if (rlen > 0u) {
                    (void)usb_dev_send(resp, rlen);
                }
            }
        }

        {
            uint32_t len = 0;
            const uint8_t *buf = capture_get_ready(&g_cap, &len);
            if (buf != NULL) {
                if (g_app.ber_running) {
                    usb_app_ber_feed(&g_app, buf, len);
                }
                (void)usb_dev_send(buf, len); /* stub: not implemented */
                capture_release(&g_cap);
            }
        }
    }
    /* never returns */
}
