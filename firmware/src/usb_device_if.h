/* usb_device_if.h - the boundary between the application protocol
 * (usb_app.c, complete) and the USB device transport.
 *
 * Implemented by usb_device_tinyusb.c on TinyUSB 0.21.0
 * (third_party/PROVENANCE.md): a CDC ACM device on the STM32H723's
 * OTG HS core behind the board's USB3300 ULPI PHY. The byte-pipe
 * semantics below are unchanged from the stub era - command frames,
 * responses and streamed capture data all share the one pipe, as
 * main.c has always used it.
 *
 * What "implemented" does NOT yet mean: enumeration has never been
 * observed on hardware. The protocol engine is a proven library,
 * but the board-level glue (ULPI pin/analog-switch setup, PHY
 * reset, RCC/PWR constants) carries the house VERIFY-against-
 * RM0468 status, and nothing about a real ULPI link, a real host's
 * chirp, or suspend/resume against a real host controller can be
 * settled without the board. firmware/BRINGUP.md is the checklist
 * for exactly that residue. (Programming the board never depended
 * on any of this: the STM32 ROM DFU bootloader is the programming
 * path, docs/02.)
 */
#ifndef USB_DEVICE_IF_H
#define USB_DEVICE_IF_H

#include <stdint.h>
#include <stddef.h>

#define USB_DEV_OK              0
#define USB_DEV_NOT_IMPLEMENTED (-100) /* retained: no longer returned
                                          by the real implementation */
#define USB_DEV_NO_DATA         (-101)
#define USB_DEV_NOT_CONNECTED   (-102) /* not enumerated (yet/any more) */
#define USB_DEV_IO_ERROR        (-103) /* init failed / host not draining */

int usb_dev_init(void);
/* Queue bytes on the bulk/control IN path to the host. */
int usb_dev_send(const uint8_t *data, size_t len);
/* Copy out received host bytes; returns byte count or an error code. */
int usb_dev_recv(uint8_t *buf, size_t cap);
int usb_dev_connected(void); /* 1 once enumerated (never, in the stub) */

#endif /* USB_DEVICE_IF_H */
