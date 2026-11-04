/*
 * startup.c - minimal Cortex-M7 startup for the STM32H723 target:
 * just enough vector table + reset flow to link and boot to main().
 * IRQ vectors beyond the core exceptions are all weakly aliased to
 * Default_Handler; real handlers (DMA, OTG HS, ...) get added at
 * bring-up as the peripherals they serve are finished.
 */
#include <stdint.h>

extern int main(void);
extern uint32_t _estack;
extern uint32_t _sidata, _sdata, _edata, _sbss, _ebss;

/* From clocks.c */
extern void board_systick_irq(void);

/* From usb_device_tinyusb.c (OTG HS global interrupt, IRQ 77 -
 * VERIFY against RM0468's NVIC map at bring-up) */
extern void OTG_HS_IRQHandler(void);

void Reset_Handler(void);
void Default_Handler(void);
static void SysTick_Handler(void);

typedef void (*handler_t)(void);

/* Vector table in its own section; linker.ld places it at the start
 * of flash (the CPU also needs VTOR pointed here if the image is ever
 * offset - at 0x08000000 it is the reset default). */
__attribute__((section(".isr_vector"), used))
static const handler_t g_vectors[] = {
    (handler_t)&_estack,      /* 0: initial stack pointer */
    Reset_Handler,            /* 1: reset */
    Default_Handler,          /* 2: NMI */
    Default_Handler,          /* 3: HardFault */
    Default_Handler,          /* 4: MemManage */
    Default_Handler,          /* 5: BusFault */
    Default_Handler,          /* 6: UsageFault */
    0, 0, 0, 0,               /* 7-10: reserved */
    Default_Handler,          /* 11: SVCall */
    Default_Handler,          /* 12: DebugMon */
    0,                        /* 13: reserved */
    Default_Handler,          /* 14: PendSV */
    SysTick_Handler,          /* 15: SysTick */
    /* Peripheral IRQs 0..76 (table slots 16..92): parked in
     * Default_Handler. No driver in rev A enables any of these; the
     * slots exist so the table reaches the one peripheral vector
     * that IS live, below - an interrupt landing past the end of a
     * short table reads garbage as its handler. If another IRQ is
     * ever enabled, give its slot a real handler in the same edit. */
    Default_Handler, Default_Handler, Default_Handler, Default_Handler,
    Default_Handler, Default_Handler, Default_Handler, Default_Handler,
    Default_Handler, Default_Handler, Default_Handler, Default_Handler,
    Default_Handler, Default_Handler, Default_Handler, Default_Handler,
    Default_Handler, Default_Handler, Default_Handler, Default_Handler,
    Default_Handler, Default_Handler, Default_Handler, Default_Handler,
    Default_Handler, Default_Handler, Default_Handler, Default_Handler,
    Default_Handler, Default_Handler, Default_Handler, Default_Handler,
    Default_Handler, Default_Handler, Default_Handler, Default_Handler,
    Default_Handler, Default_Handler, Default_Handler, Default_Handler,
    Default_Handler, Default_Handler, Default_Handler, Default_Handler,
    Default_Handler, Default_Handler, Default_Handler, Default_Handler,
    Default_Handler, Default_Handler, Default_Handler, Default_Handler,
    Default_Handler, Default_Handler, Default_Handler, Default_Handler,
    Default_Handler, Default_Handler, Default_Handler, Default_Handler,
    Default_Handler, Default_Handler, Default_Handler, Default_Handler,
    Default_Handler, Default_Handler, Default_Handler, Default_Handler,
    Default_Handler, Default_Handler, Default_Handler, Default_Handler,
    Default_Handler, Default_Handler, Default_Handler, Default_Handler,
    Default_Handler,
    /* IRQ 77 (slot 93): USB OTG HS global interrupt - the only
     * peripheral interrupt the firmware enables (via TinyUSB). */
    OTG_HS_IRQHandler,
};

static void SysTick_Handler(void)
{
    board_systick_irq();
}

__attribute__((weak)) void SystemInit(void)
{
    /* Enable the Cortex-M7 FPU (CP10/CP11 full access in the SCB
     * CPACR, architectural register at 0xE000ED88). This is REQUIRED,
     * not an optimisation: the build uses the hard-float ABI, so
     * compiled float instructions in hv_ctrl/usb_app would fault on
     * first use with the FPU still disabled. Clock setup itself lives
     * in clocks_init(), called from main(). */
    *(volatile uint32_t *)0xE000ED88u |= (0xFu << 20);
    __asm__ volatile ("dsb");
    __asm__ volatile ("isb");
}

void Reset_Handler(void)
{
    uint32_t *src;
    uint32_t *dst;
    SystemInit();
    src = &_sidata;
    for (dst = &_sdata; dst < &_edata; dst++) {
        *dst = *src;
        src++;
    }
    for (dst = &_sbss; dst < &_ebss; dst++) {
        *dst = 0u;
    }
    (void)main();
    for (;;) {
        /* main() never returns; if it ever does, park here. */
    }
}

void Default_Handler(void)
{
    for (;;) {
        /* Park: a fault in a system with HV attached should stop,
         * not wander. HV_EN defaults low and is only raised by the
         * control loop, which is no longer running. */
    }
}
