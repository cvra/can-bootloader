#include <stdint.h>
#include <libopencm3/cm3/scb.h>
#include <boot_arg.h>

#define BOOT_ARG_MAGIC_VALUE_LO 0x01234567
#define BOOT_ARG_MAGIC_VALUE_HI 0x0089abcd

void reboot_system(uint8_t arg)
{
    uint32_t* ram_start = (uint32_t*)0x20000000;

    ram_start[0] = BOOT_ARG_MAGIC_VALUE_LO;
    ram_start[1] = BOOT_ARG_MAGIC_VALUE_HI | (arg << 24);

    scb_reset_system();
}
