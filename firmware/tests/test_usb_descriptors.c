/*
 * test_usb_descriptors.c - host audit of the USB descriptors in
 * src/usb_descriptors_data.h (the same bytes the firmware serves
 * through TinyUSB). No stack involved: this walks the raw arrays
 * and checks them against the USB 2.0 / CDC rules that hosts
 * enforce during enumeration - the class of bug that makes a device
 * enumerate on one laptop and not another is usually sitting in
 * these bytes, and bytes can be checked without hardware.
 */
#include <stdio.h>
#include <string.h>

#include "usb_descriptors_data.h"

static int failures = 0;

#define CHECK(cond, name)                                              \
    do {                                                               \
        if (cond) {                                                    \
            printf("PASS %s\n", (name));                               \
        } else {                                                       \
            printf("FAIL %s (line %d)\n", (name), __LINE__);           \
            failures++;                                                \
        }                                                              \
    } while (0)

static uint16_t u16le(const uint8_t *p)
{
    return (uint16_t)((uint16_t)p[0] | ((uint16_t)p[1] << 8));
}

/* Walk one configuration descriptor set. Returns (via the counts)
 * the structure found; *ok clears on any malformed length chain. */
struct walk {
    int interfaces;
    int endpoints;
    int iad;
    int func_header, func_call, func_acm, func_union;
    int seen_notif, seen_out, seen_in;
    uint16_t bulk_mps;
    int bad;
};

static void walk_config(const uint8_t *cfg, size_t total,
                        struct walk *w)
{
    size_t off = 0;
    memset(w, 0, sizeof *w);
    if (total < 9u || cfg[0] != 9u || cfg[1] != 2u) {
        w->bad = 1;
        return;
    }
    if ((size_t)u16le(cfg + 2) != total) {
        w->bad = 1; /* wTotalLength disagrees with the array */
        return;
    }
    while (off < total) {
        uint8_t len = cfg[off];
        uint8_t type;
        if (len < 2u || off + len > total) {
            w->bad = 1;
            return;
        }
        type = cfg[off + 1];
        if (type == 0x0Bu) {           /* IAD */
            w->iad++;
            if (cfg[off + 2] != 0u || cfg[off + 3] != 2u
                || cfg[off + 4] != 0x02u || cfg[off + 5] != 0x02u) {
                w->bad = 1;
            }
        } else if (type == 4u) {       /* INTERFACE */
            w->interfaces++;
        } else if (type == 5u) {       /* ENDPOINT */
            uint8_t addr = cfg[off + 2];
            uint8_t attr = cfg[off + 3];
            uint16_t mps = u16le(cfg + off + 4);
            w->endpoints++;
            if (addr == USB_EP_CDC_NOTIF) {
                w->seen_notif = 1;
                if ((attr & 0x03u) != 0x03u || mps != USB_CDC_NOTIF_MPS) {
                    w->bad = 1; /* notif must be interrupt, 8 B */
                }
            } else if (addr == USB_EP_CDC_OUT || addr == USB_EP_CDC_IN) {
                if ((attr & 0x03u) != 0x02u) {
                    w->bad = 1; /* data endpoints must be bulk */
                }
                if (w->bulk_mps != 0u && w->bulk_mps != mps) {
                    w->bad = 1; /* IN and OUT sizes must agree */
                }
                w->bulk_mps = mps;
                if (addr == USB_EP_CDC_OUT) {
                    w->seen_out = 1;
                } else {
                    w->seen_in = 1;
                }
            } else {
                w->bad = 1; /* endpoint the design does not know */
            }
        } else if (type == 0x24u) {    /* CS_INTERFACE functional */
            switch (cfg[off + 2]) {
            case 0x00: w->func_header = 1; break;
            case 0x01: w->func_call = 1; break;
            case 0x02: w->func_acm = 1; break;
            case 0x06:
                w->func_union = 1;
                if (cfg[off + 3] != 0u || cfg[off + 4] != 1u) {
                    w->bad = 1; /* union must bind interfaces 0+1 */
                }
                break;
            default: w->bad = 1; break;
            }
        }
        off += len;
    }
    if (off != total) {
        w->bad = 1;
    }
}

static void audit_config(const char *name, const uint8_t *cfg,
                         size_t total, uint16_t want_bulk_mps)
{
    struct walk w;
    char buf[96];
    walk_config(cfg, total, &w);

    snprintf(buf, sizeof buf, "%s: length chain + wTotalLength consistent",
             name);
    CHECK(!w.bad, buf);
    snprintf(buf, sizeof buf, "%s: 2 interfaces under one IAD", name);
    CHECK(w.interfaces == 2 && w.iad == 1, buf);
    snprintf(buf, sizeof buf,
             "%s: all four CDC functional descriptors present", name);
    CHECK(w.func_header && w.func_call && w.func_acm && w.func_union, buf);
    snprintf(buf, sizeof buf, "%s: notif + bulk OUT + bulk IN endpoints",
             name);
    CHECK(w.endpoints == 3 && w.seen_notif && w.seen_out && w.seen_in, buf);
    snprintf(buf, sizeof buf, "%s: bulk max packet size is %u", name,
             (unsigned)want_bulk_mps);
    CHECK(w.bulk_mps == want_bulk_mps, buf);
    snprintf(buf, sizeof buf, "%s: config header sane (bus powered, "
             "bMaxPower <= 500 mA)", name);
    CHECK(cfg[7] == 0x80u && cfg[8] >= 1u && cfg[8] <= 250u, buf);
}

int main(void)
{
    /* Device descriptor */
    CHECK(usb_desc_device[0] == 18u && usb_desc_device[1] == 1u,
          "device descriptor: 18 bytes, type DEVICE");
    CHECK(u16le(usb_desc_device + 8) == USB_VID
          && u16le(usb_desc_device + 10) == USB_PID,
          "device descriptor: VID/PID match the recorded development ids");
    CHECK(usb_desc_device[7] == USB_EP0_MPS,
          "device descriptor: EP0 max packet 64");
    CHECK(usb_desc_device[17] == 1u,
          "device descriptor: one configuration");
    CHECK(usb_desc_device[14] >= 1u && usb_desc_device[14] <= USB_STR_COUNT
          && usb_desc_device[15] <= USB_STR_COUNT
          && usb_desc_device[16] <= USB_STR_COUNT,
          "device descriptor: string indices within the string table");

    /* Device qualifier mirrors the device descriptor class triple */
    CHECK(usb_desc_device_qualifier[0] == 10u
          && usb_desc_device_qualifier[1] == 6u
          && usb_desc_device_qualifier[4] == usb_desc_device[4]
          && usb_desc_device_qualifier[5] == usb_desc_device[5]
          && usb_desc_device_qualifier[6] == usb_desc_device[6]
          && usb_desc_device_qualifier[7] == USB_EP0_MPS,
          "device qualifier: 10 bytes, class triple mirrors device");

    /* Both speed configurations, against their own legal bulk size */
    audit_config("config HS", usb_desc_configuration_hs,
                 sizeof usb_desc_configuration_hs, USB_BULK_MPS_HS);
    audit_config("config FS", usb_desc_configuration_fs,
                 sizeof usb_desc_configuration_fs, USB_BULK_MPS_FS);

    /* The two configurations must differ ONLY in the bulk MPS fields
     * (offsets of the two wMaxPacketSize low bytes in the layout). */
    {
        size_t i;
        int diffs = 0;
        for (i = 0; i < sizeof usb_desc_configuration_hs; i++) {
            if (usb_desc_configuration_hs[i] != usb_desc_configuration_fs[i]) {
                diffs++;
            }
        }
        /* 2 endpoints x (low + high byte of 512 vs 64) = 4 bytes */
        CHECK(diffs == 4, "config HS vs FS: differ only in bulk MPS bytes");
    }

    if (failures == 0) {
        printf("RESULT: ALL TESTS PASSED\n");
        return 0;
    }
    printf("RESULT: %d FAILURE(S)\n", failures);
    return 1;
}
