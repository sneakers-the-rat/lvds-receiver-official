/*
 * usb_device_stub.c - explicit stub for usb_device_if.h.
 * Every function says, in code, that USB is not implemented yet.
 * See usb_device_if.h for the bring-up sequence that replaces this.
 */
#include "usb_device_if.h"

int usb_dev_init(void)
{
    return USB_DEV_NOT_IMPLEMENTED;
}

int usb_dev_send(const uint8_t *data, size_t len)
{
    (void)data;
    (void)len;
    return USB_DEV_NOT_IMPLEMENTED;
}

int usb_dev_recv(uint8_t *buf, size_t cap)
{
    (void)buf;
    (void)cap;
    return USB_DEV_NOT_IMPLEMENTED;
}

int usb_dev_connected(void)
{
    return 0;
}
