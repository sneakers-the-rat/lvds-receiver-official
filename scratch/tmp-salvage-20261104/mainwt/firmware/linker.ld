/*
 * linker.ld - STM32H723ZG memory map, per the datasheet for the ZG
 * variant: 1 MB flash at 0x08000000, 128 KB DTCM at 0x20000000,
 * 512 KB AXI SRAM at 0x24000000. VERIFY against the exact ordered
 * variant's datasheet at bring-up (H723 flash/RAM sizes differ by
 * variant letter).
 */
ENTRY(Reset_Handler)

MEMORY
{
    FLASH   (rx)  : ORIGIN = 0x08000000, LENGTH = 1024K
    DTCM    (rwx) : ORIGIN = 0x20000000, LENGTH = 128K
    AXI_SRAM (rwx): ORIGIN = 0x24000000, LENGTH = 512K
}

_estack = ORIGIN(DTCM) + LENGTH(DTCM);

SECTIONS
{
    .isr_vector :
    {
        KEEP(*(.isr_vector))
    } > FLASH

    .text :
    {
        *(.text*)
        *(.rodata*)
        . = ALIGN(4);
    } > FLASH

    .ARM.extab : { *(.ARM.extab* .gnu.linkonce.armextab.*) } > FLASH
    .ARM.exidx :
    {
        *(.ARM.exidx* .gnu.linkonce.armexidx.*)
    } > FLASH

    _sidata = LOADADDR(.data);
    .data :
    {
        . = ALIGN(4);
        _sdata = .;
        *(.data*)
        . = ALIGN(4);
        _edata = .;
    } > DTCM AT > FLASH

    .bss :
    {
        . = ALIGN(4);
        _sbss = .;
        *(.bss*)
        *(COMMON)
        . = ALIGN(4);
        _ebss = .;
    } > DTCM

    /* Capture double buffer (capture.c) and any future DMA buffers. */
    .axi_sram (NOLOAD) :
    {
        . = ALIGN(32);
        *(.axi_sram*)
        . = ALIGN(32);
    } > AXI_SRAM

    /DISCARD/ :
    {
        *(.note*)
        *(.comment*)
    }
}
