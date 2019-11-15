#include <stdint.h>

extern uint32_t _sbss;
extern uint32_t _ebss;
extern uint32_t _sdata;
extern uint32_t _edata;
extern uint32_t _ldata;
extern uint32_t _eram;

extern void platform_main(int);
extern void fault_handler(void);
extern void reset_handler(void);

__attribute__((section(".vectors"))) void (*const vector_table[])(void) = {
    (void*)&_eram,
    reset_handler,
    fault_handler, // nmi_handler
    fault_handler, // hard_fault_handler
    fault_handler, // mem_manage_handler
    fault_handler, // bus_fault_handler
    fault_handler, // usage_fault_handler
};

void __attribute__((naked)) bootloader_startup(int arg)
{
    volatile uint32_t *p_ram, *p_flash;
    // clear .bss section
    p_ram = &_sbss;
    while (p_ram < &_ebss) {
        *p_ram++ = 0;
    }
    // copy .data section from flash to ram
    p_flash = &_ldata;
    p_ram = &_sdata;
    while (p_ram < &_edata) {
        *p_ram++ = *p_flash++;
    }

    platform_main(arg);

    while (1)
        ;
}
