
#include <libopencm3/stm32/flash.h>
#include "flash_writer.h"

#if !defined(FLASH_PROGRAM_SIZE)
// flash parallel program size, depends on VCC
// 0 (8-bit), 1 (16-bit), 2 (32-bit), 3 (64-bit)
#define FLASH_PROGRAM_SIZE 0 // default: 8-bit
#endif

static uint8_t flash_addr_to_sector(uint32_t addr)
{
    uint8_t sector;
    uint32_t offset = addr & 0xFFFFFF;
    if (offset < 0x10000) {
        sector = offset / 0x4000; // 16K sectors, 0x08000000 to 0x0800FFFF
    } else if (offset < 0x20000) {
        sector = 3 + offset / 0x10000; // 64K sector, 0x08010000 to 0x0801FFFF
    } else {
        sector = 4 + offset / 0x20000; // 128K sectors, 0x08010000 to 0x080FFFFF
    }
    if (addr >= 0x08100000) {
        // Bank 2, same layout, starting at 0x08100000
        sector += 12;
    }
    return sector;
}

void flash_writer_unlock(void)
{
    flash_unlock();
}

void flash_writer_lock(void)
{
    flash_lock();
}

void flash_writer_page_erase(void *page)
{
    uint8_t sector = flash_addr_to_sector((uint32_t)page);
    flash_erase_sector(sector, FLASH_PROGRAM_SIZE);
}

void flash_writer_page_write(void *page, void *data, size_t len)
{
    flash_program((uint32_t)page, data, len);
}
