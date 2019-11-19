#include <libopencm3/stm32/flash.h>
#include "flash_writer.h"

void flash_init(void)
{
}

void flash_writer_unlock(void)
{
    flash_unlock();
}

void flash_writer_lock(void)
{
    flash_lock();
}

void flash_writer_page_erase(void* page)
{
    flash_wait_for_last_operation();

    FLASH_CR |= FLASH_CR_PER;
    FLASH_AR = (uint32_t)page;
    FLASH_CR |= FLASH_CR_STRT;

    flash_wait_for_last_operation();

    FLASH_CR &= ~FLASH_CR_PER;
}

static void flash_write_half_word(uint16_t* flash, uint16_t half_word)
{
    /* select flash programming */
    FLASH_CR |= FLASH_CR_PG;

    /* perform half-word write */
    *flash = half_word;

    flash_wait_for_last_operation();
}

/* page address is assumed to be half-word aligned */
void flash_writer_page_write(void* page, void* data, size_t len)
{
    uint8_t* bytes = (uint8_t*)data;
    uint16_t* flash = (uint16_t*)page;
    uint16_t half_word;

    flash_wait_for_last_operation();

    size_t count;
    for (count = len; count > 1; count -= 2) {
        half_word = *bytes++;
        half_word |= (uint16_t)*bytes++ << 8;

        flash_write_half_word(flash++, half_word);
    }

    if (count == 1) {
        half_word = *bytes;
        /* preserve value of adjacent byte */
        half_word |= (uint16_t)(*(uint8_t*)flash) << 8;

        flash_write_half_word(flash, half_word);
    }

    /* reset flags */
    FLASH_CR &= ~FLASH_CR_PG;
    FLASH_SR |= FLASH_SR_EOP;
}
