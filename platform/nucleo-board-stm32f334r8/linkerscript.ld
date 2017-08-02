/*
 * Linker file for the STM32F334R8 microcontroller
 * http://www.st.com/en/microcontrollers/stm32f334r8.html
 *
 * 64K flash memory, 12K RAM, 4K CCRAM
 * Flash page size: 2K (= 0x800)
 *
 * TODO: Complete section definitions below with definitions for CCRAM 
 */

MEMORY
{
    FLASH_TEXT    (RX) : ORIGIN = 0x08000000, LENGTH = 20K
    FLASH_CONFIG1 (RX) : ORIGIN = 0x08005000, LENGTH = 2K
    FLASH_CONFIG2 (RX) : ORIGIN = 0x08005800, LENGTH = 2K
    FLASH_APP     (RX) : ORIGIN = 0x08006000, LENGTH = 40K
    RAM          (RWX) : ORIGIN = 0x20000000, LENGTH = 12K
    CCRAM        (RWX) : ORIGIN = 0x10000000, LENGTH = 4K
}

REGION_ALIAS("REGION_TEXT",   FLASH_TEXT);
REGION_ALIAS("REGION_RODATA", FLASH_TEXT);
REGION_ALIAS("REGION_DATA",   RAM);
REGION_ALIAS("REGION_BSS",    RAM);
REGION_ALIAS("REGION_NOINIT", RAM);

EXTERN(vector_table)

ENTRY(reset_handler)

SECTIONS
{
    /* flash memory boundaries */
    flash_begin = ORIGIN(FLASH_TEXT);
    flash_end = ORIGIN(FLASH_APP) + LENGTH(FLASH_APP);

    /* config flash page */
    config_page1 = ORIGIN(FLASH_CONFIG1);
    config_page2 = ORIGIN(FLASH_CONFIG2);

    /* application in flash */
    application_address = ORIGIN(FLASH_APP);
    application_size = LENGTH(FLASH_APP);

    .text :
    {
        *(.vectors) /* vector_table */

        _stext = .;

        CREATE_OBJECT_SYMBOLS

        *(.text .text.*)        /* Program code */
        *(.gnu.linkonce.t.*)


        *(.plt)
        *(.gnu.warning)
        *(.glue_7t) *(.glue_7) *(.vfp11_veneer)

        *(.ARM.extab* .gnu.linkonce.armextab.*)
        *(.gcc_except_table)
        *(.eh_frame_hdr)
        *(.eh_frame)

        . = ALIGN(4);
        KEEP(*(.init))

        . = ALIGN(4);
        __preinit_array_start = .;
        KEEP (*(.preinit_array))
        __preinit_array_end = .;

        . = ALIGN(4);
        __init_array_start = .;
        KEEP (*(SORT(.init_array.*)))
        KEEP (*(.init_array))
        __init_array_end = .;

        . = ALIGN(4);
        KEEP (*crtbegin.o(.ctors))
        KEEP (*(EXCLUDE_FILE (*crtend.o) .ctors))
        KEEP (*(SORT(.ctors.*)))
        KEEP (*crtend.o(.ctors))

        . = ALIGN(4);
        KEEP(*(.fini))

        . = ALIGN(4);
        __fini_array_start = .;
        KEEP (*(.fini_array))
        KEEP (*(SORT(.fini_array.*)))
        __fini_array_end = .;

        KEEP (*crtbegin.o(.dtors))
        KEEP (*(EXCLUDE_FILE (*crtend.o) .dtors))
        KEEP (*(SORT(.dtors.*)))
        KEEP (*crtend.o(.dtors))

        . = ALIGN(4);
        _etext = .;
    } > REGION_TEXT

    .rodata :
    {
        . = ALIGN(4);
        KEEP(*(.rodata.keep .rodata.keep.*))
        *(.rodata .rodata.*)    /* Read only data */
        . = ALIGN(4);
    } > REGION_RODATA

    /*
     * .ARM.exidx exception unwinding; mandated by ARM's C++ ABI
     */
    __exidx_start = .;
    .ARM.exidx :
      {
        *(.ARM.exidx* .gnu.linkonce.armexidx.*)
      } > REGION_RODATA
    __exidx_end = .;

    .data :
    {
        . = ALIGN(4);
        _sdata = .;
        _data = _sdata;

        *(.got.plt) *(.got)

        *(.data .data.*)        /* Data memory */
        *(.gnu.linkonce.d.*)

        . = ALIGN(4);
        *(.fastrun .fastrun.*)  /* Functions in RAM */

        . = ALIGN(4);
        _edata = .;
    } > REGION_DATA AT > REGION_RODATA
    _ldata = LOADADDR(.data);
    _data_loadaddr = _ldata;

    .bss :
    {
        . = ALIGN(4);
        _sbss = .;

        *(.bss .bss.*)          /* Zero-filled data memory */
        *(.gnu.linkonce.b.*)

        . = ALIGN(4);
        _ebss = .;
    } > REGION_BSS

    .noinit :
    {
        _snoinit = .;
        . = ALIGN(4);

        *(.noinit .noinit.*)

        . = ALIGN(4);
        _enoinit = .;
    } > REGION_NOINIT

    . = ALIGN(8);
    _sheap = .;
    _sstack = .;

    /* default stack at the end of RAM */
    _eram = ORIGIN(RAM) + LENGTH(RAM);
    _eheap = _eram;
    _estack = _eram;
    _stack = _eram;

    /*
     * Debugging sections
     */
    .stab 0 (NOLOAD) : { *(.stab) }
    .stabstr 0 (NOLOAD) : { *(.stabstr) }
    /* DWARF debug sections.
     * Symbols in the DWARF debugging sections are relative to the beginning
     * of the section so we begin them at 0.  */
    /* DWARF 1 */
    .debug          0 : { *(.debug) }
    .line           0 : { *(.line) }
    /* GNU DWARF 1 extensions */
    .debug_srcinfo  0 : { *(.debug_srcinfo) }
    .debug_sfnames  0 : { *(.debug_sfnames) }
    /* DWARF 1.1 and DWARF 2 */
    .debug_aranges  0 : { *(.debug_aranges) }
    .debug_pubnames 0 : { *(.debug_pubnames) }
    /* DWARF 2 */
    .debug_info     0 : { *(.debug_info .gnu.linkonce.wi.*) }
    .debug_abbrev   0 : { *(.debug_abbrev) }
    .debug_line     0 : { *(.debug_line) }
    .debug_frame    0 : { *(.debug_frame) }
    .debug_str      0 : { *(.debug_str) }
    .debug_loc      0 : { *(.debug_loc) }
    .debug_macinfo  0 : { *(.debug_macinfo) }
    /* SGI/MIPS DWARF 2 extensions */
    .debug_weaknames 0 : { *(.debug_weaknames) }
    .debug_funcnames 0 : { *(.debug_funcnames) }
    .debug_typenames 0 : { *(.debug_typenames) }
    .debug_varnames  0 : { *(.debug_varnames) }

    .note.gnu.arm.ident 0 : { KEEP (*(.note.gnu.arm.ident)) }
    .ARM.attributes 0 : { KEEP (*(.ARM.attributes)) }
    /DISCARD/ : { *(.note.GNU-stack) }
}
