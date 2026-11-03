/* usb_device_if.h - the boundary between the application protocol
 * (usb_app.c, complete) and the USB device stack (NOT implemented).
 *
 * What remains to implement this layer at bring-up, and why it is not
 * faked here:
 *   The board uses the STM32H723's USB OTG HS core with an external
 *   Microchip USB3300 ULPI PHY. A working device stack requires, in
 *   order:
 *     1. GPIO alternate-function setup for the ULPI bus (D0-D7, CLK,
 *        DIR, NXT, STP) and the USB3300 reset/clock bring-up
 *        (24 MHz crystal on the PHY, 60 MHz ULPI clock out).
 *     2. RCC: OTG HS + ULPI clocks, and the H723's power/voltage
 *        detector bits for USB.
 *     3. OTG HS core initialisation: AHB/TRDT configuration, device
 *        mode force, FIFO sizing (RX / TX0..n), endpoint 0 setup.
 *     4. A USB device protocol engine: reset/suspend interrupts,
 *        SETUP packet handling, enumeration descriptors (device,
 *        configuration, string), SET_ADDRESS / SET_CONFIGURATION.
 *     5. Two interfaces on top of that: bulk IN for streaming
 *        (capture data) and a control/CDC-style channel on which the
 *        byte buffers of usb_app_process() are carried.
 *   That is several thousand lines of register-level code that can
 *   only be debugged against a real ULPI link and a USB analyser /
 *   host. Writing an untestable imitation of it here would compile
 *   and lie. So: usb_device_stub.c implements this interface with
 *   explicit USB_DEV_NOT_IMPLEMENTED returns, main.c copes with that,
 *   and enumeration does NOT work until this layer is written at
 *   bring-up. (Programming the board does not depend on it: the
 *   STM32 ROM DFU bootloader is the programming path, docs/02.)
 */
#ifndef USB_DEVICE_IF_H
#define USB_DEVICE_IF_H

#include <stdint.h>
#include <stddef.h>

#define USB_DEV_OK              0
#define USB_DEV_NOT_IMPLEMENTED (-100)
#define USB_DEV_NO_DATA         (-101)

int usb_dev_init(void);
/* Queue bytes on the bulk/control IN path to the host. */
int usb_dev_send(const uint8_t *data, size_t len);
/* Copy out received host bytes; returns byte count or an error code. */
int usb_dev_recv(uint8_t *buf, size_t cap);
int usb_dev_connected(void); /* 1 once enumerated (never, in the stub) */

#endif /* USB_DEVICE_IF_H */
