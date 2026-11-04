/*
 * tusb_config.h - TinyUSB configuration for the PDLVDS-RX firmware.
 * Stack provenance: third_party/PROVENANCE.md (TinyUSB 0.21.0).
 *
 * Device-only, root hub port 0 = the STM32H723's single OTG HS core
 * behind the USB3300 ULPI PHY, one CDC ACM interface pair.
 */
#ifndef TUSB_CONFIG_H
#define TUSB_CONFIG_H

#ifdef __cplusplus
extern "C" {
#endif

/* MCU + OS selection. OPT_MCU_STM32H7 makes TinyUSB's DWC2 port use
 * its stm32h7 register map; the CMSIS symbols that port expects are
 * supplied by tinyusb_port/stm32h7xx.h (a shim, see its header). */
#define CFG_TUSB_MCU            OPT_MCU_STM32H7
#define CFG_TUSB_OS             OPT_OS_NONE

/* Port 0, device mode, high speed. On the single-OTG H723 the DWC2
 * port table aliases port 0 onto the HS core (see the shim header).
 * If the link negotiates full speed instead, the stack serves the
 * full-speed configuration descriptor (usb_descriptors.c). */
#define CFG_TUSB_RHPORT0_MODE   (OPT_MODE_DEVICE | OPT_MODE_HIGH_SPEED)

/* DWC2 data path: SLAVE mode (the CPU copies the FIFOs), DMA off.
 * Reason: this firmware's .bss/.data live in DTCM (linker.ld), which
 * the OTG DMA engine cannot address, and slave mode also sidesteps
 * Cortex-M7 D-cache coherency for DMA buffers entirely. A 550 MHz
 * Cortex-M7 copying FIFO words sustains our bulk rates; if stream
 * throughput on hardware ever proves CPU-bound, moving the TinyUSB
 * buffers to AXI SRAM + enabling DMA is the documented follow-up
 * (firmware/BRINGUP.md). */
#define CFG_TUD_DWC2_SLAVE_ENABLE 1
#define CFG_TUD_DWC2_DMA_ENABLE   0

/* Classes: CDC only. */
#define CFG_TUD_CDC               1
#define CFG_TUD_MSC               0
#define CFG_TUD_HID               0
#define CFG_TUD_MIDI              0
#define CFG_TUD_VENDOR            0

#define CFG_TUD_ENDPOINT0_SIZE    64

/* CDC buffering. RX carries command frames (<= 64 B by the host
 * protocol's design, oversized input simply stays queued). TX is
 * written in bursts of up to one 8 KiB capture buffer per call;
 * usb_dev_send() drains it chunk by chunk, so 2 KiB of FIFO is a
 * pacing buffer, not a limit. Buffers live in DTCM (.bss) - fine in
 * slave mode, see above. */
#define CFG_TUD_CDC_RX_BUFSIZE    512
#define CFG_TUD_CDC_TX_BUFSIZE    2048
#define CFG_TUD_CDC_EP_BUFSIZE    512

#ifdef __cplusplus
}
#endif

#endif /* TUSB_CONFIG_H */
