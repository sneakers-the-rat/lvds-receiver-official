/*
 * usb_descriptors_data.h - USB descriptor bytes for PDLVDS-RX.
 *
 * Plain data, no stack dependency: usb_descriptors.c hands these
 * arrays to TinyUSB, and tests/test_usb_descriptors.c audits them
 * on the host. If you change a byte here, both see the change.
 *
 * Device shape: one CDC ACM function (communication interface +
 * data interface, joined by an IAD). Commands, responses and the
 * streamed capture data all travel on the CDC data pipe, exactly as
 * the byte-pipe contract of usb_device_if.h (and main.c's use of
 * it) has always defined; the protocol framing is usb_app.h's.
 *
 * VID/PID - DEVELOPMENT IDS, NOT REGISTERED. 0x1209 is the VID
 * pid.codes provides for open-source hardware; PID 0xD723 is an
 * unregistered placeholder chosen for this prototype. Register a
 * PID (pid.codes) or obtain a VID before distributing hardware
 * with this firmware - see firmware/BRINGUP.md.
 *
 * Power: bMaxPower declares 500 mA, the maximum a USB 2.0 device
 * may declare. docs/03's board budget (< 4.5 W) exceeds that; the
 * tension is recorded in firmware/BRINGUP.md as a design-review
 * item, not silently resolved here.
 */
#ifndef USB_DESCRIPTORS_DATA_H
#define USB_DESCRIPTORS_DATA_H

#include <stdint.h>

#define USB_VID              0x1209u
#define USB_PID              0xD723u
#define USB_BCD_DEVICE       0x0100u

#define USB_EP_CDC_NOTIF     0x81u  /* interrupt IN, 8 B */
#define USB_EP_CDC_OUT       0x02u  /* bulk OUT */
#define USB_EP_CDC_IN        0x82u  /* bulk IN */
#define USB_CDC_NOTIF_MPS    8u
#define USB_BULK_MPS_HS      512u   /* the only legal HS bulk size */
#define USB_BULK_MPS_FS      64u    /* the largest legal FS bulk size */
#define USB_EP0_MPS          64u

static const uint8_t usb_desc_device[18] = {
    18,          /* bLength */
    1,           /* bDescriptorType: DEVICE */
    0x00, 0x02,  /* bcdUSB 2.00 */
    0xEF,        /* bDeviceClass: miscellaneous (IAD) */
    0x02,        /* bDeviceSubClass: common class */
    0x01,        /* bDeviceProtocol: interface association */
    USB_EP0_MPS, /* bMaxPacketSize0 */
    (uint8_t)(USB_VID & 0xFFu), (uint8_t)(USB_VID >> 8),
    (uint8_t)(USB_PID & 0xFFu), (uint8_t)(USB_PID >> 8),
    (uint8_t)(USB_BCD_DEVICE & 0xFFu), (uint8_t)(USB_BCD_DEVICE >> 8),
    1,           /* iManufacturer */
    2,           /* iProduct */
    3,           /* iSerialNumber */
    1            /* bNumConfigurations */
};

/* Device qualifier: what a host negotiating high speed asks for
 * before chirp completes. Mirrors the device descriptor's class
 * triple, as USB 2.0 requires. */
static const uint8_t usb_desc_device_qualifier[10] = {
    10,          /* bLength */
    6,           /* bDescriptorType: DEVICE_QUALIFIER */
    0x00, 0x02,  /* bcdUSB 2.00 */
    0xEF, 0x02, 0x01,
    USB_EP0_MPS,
    1,           /* bNumConfigurations */
    0            /* reserved */
};

/* One CDC ACM function, laid out byte-for-byte as TinyUSB's
 * TUD_CDC_DESCRIPTOR template (usbd.h) expands it, parameterised
 * only by the bulk max packet size so the high-speed (512) and
 * full-speed (64) configurations differ exactly where USB requires
 * them to. Total length: 9 (config) + 66 (function) = 75. */
#define USB_DESC_CONFIGURATION(mps) { \
    /* configuration header */ \
    9, 2, 75, 0, 2, 1, 0, 0x80, 250, \
    /* interface association descriptor */ \
    8, 0x0B, 0, 2, 0x02, 0x02, 0x00, 0, \
    /* CDC communication interface */ \
    9, 4, 0, 0, 1, 0x02, 0x02, 0x00, 4, \
    /* CDC header functional descriptor, bcdCDC 1.20 */ \
    5, 0x24, 0x00, 0x20, 0x01, \
    /* CDC call management functional descriptor */ \
    5, 0x24, 0x01, 0x00, 1, \
    /* CDC abstract control management functional descriptor */ \
    4, 0x24, 0x02, 0x06, \
    /* CDC union functional descriptor */ \
    5, 0x24, 0x06, 0, 1, \
    /* notification endpoint (interrupt IN) */ \
    7, 5, USB_EP_CDC_NOTIF, 0x03, USB_CDC_NOTIF_MPS, 0, 1, \
    /* CDC data interface */ \
    9, 4, 1, 0, 2, 0x0A, 0x00, 0x00, 0, \
    /* bulk OUT endpoint */ \
    7, 5, USB_EP_CDC_OUT, 0x02, (uint8_t)((mps) & 0xFFu), \
        (uint8_t)(((mps) >> 8) & 0xFFu), 0, \
    /* bulk IN endpoint */ \
    7, 5, USB_EP_CDC_IN, 0x02, (uint8_t)((mps) & 0xFFu), \
        (uint8_t)(((mps) >> 8) & 0xFFu), 0 \
}

static const uint8_t usb_desc_configuration_hs[75] =
    USB_DESC_CONFIGURATION(USB_BULK_MPS_HS);
static const uint8_t usb_desc_configuration_fs[75] =
    USB_DESC_CONFIGURATION(USB_BULK_MPS_FS);

/* String descriptors (ASCII here; usb_descriptors.c widens them to
 * the UTF-16LE form USB carries). Index 0 is the language list. */
#define USB_STR_LANGID     0x0409u /* en-US */
static const char *const usb_desc_strings[] = {
    "PDLVDS",              /* 1: manufacturer */
    "PDLVDS-RX rev A",     /* 2: product */
    "0001",                /* 3: serial (placeholder, see BRINGUP) */
    "PDRX control + data"  /* 4: CDC interface */
};
#define USB_STR_COUNT 4u

#endif /* USB_DESCRIPTORS_DATA_H */
