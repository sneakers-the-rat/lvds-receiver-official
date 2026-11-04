/*
 * usb_descriptors.c - TinyUSB descriptor callbacks.
 *
 * The bytes themselves live in usb_descriptors_data.h (audited on
 * the host by tests/test_usb_descriptors.c); this file only selects
 * and serves them. The configuration descriptor is speed-dependent:
 * a high-speed link gets the 512-byte bulk configuration, a
 * full-speed link the 64-byte one, and each speed's
 * "other speed configuration" request gets the opposite set, as
 * USB 2.0 intends.
 */
#include <string.h>

#include "tusb.h"
#include "usb_descriptors_data.h"

const uint8_t *tud_descriptor_device_cb(void)
{
    return usb_desc_device;
}

const uint8_t *tud_descriptor_configuration_cb(uint8_t index)
{
    (void)index; /* only configuration 0 exists */
    return (tud_speed_get() == TUSB_SPEED_HIGH)
               ? usb_desc_configuration_hs
               : usb_desc_configuration_fs;
}

const uint8_t *tud_descriptor_device_qualifier_cb(void)
{
    return usb_desc_device_qualifier;
}

const uint8_t *tud_descriptor_other_speed_configuration_cb(uint8_t index)
{
    (void)index;
    return (tud_speed_get() == TUSB_SPEED_HIGH)
               ? usb_desc_configuration_fs
               : usb_desc_configuration_hs;
}

/* String descriptors: index 0 is the language ID list, the rest are
 * widened from the ASCII table in the data header into a static
 * buffer (one at a time - TinyUSB consumes each before asking for
 * the next). */
const uint16_t *tud_descriptor_string_cb(uint8_t index, uint16_t langid)
{
    static uint16_t desc[32];
    const char *str;
    uint8_t i, count;

    (void)langid; /* en-US only */
    if (index == 0u) {
        desc[0] = (uint16_t)((3u << 8) | 4u); /* type 3, 4 bytes */
        desc[1] = USB_STR_LANGID;
        return desc;
    }
    if (index > USB_STR_COUNT) {
        return NULL;
    }
    str = usb_desc_strings[index - 1u];
    count = (uint8_t)strlen(str);
    if (count > 31u) {
        count = 31u;
    }
    desc[0] = (uint16_t)((3u << 8) | (uint16_t)(2u + 2u * count));
    for (i = 0; i < count; i++) {
        desc[1u + i] = (uint8_t)str[i];
    }
    return desc;
}
