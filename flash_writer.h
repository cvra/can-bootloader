
#ifndef FLASH_WRITER_H
#define FLASH_WRITER_H

#include <stdint.h>
#include <stddef.h>

/** Unlocks the flash for programming. */
void flash_writer_unlock(void);

/** Locks the flash */
void flash_writer_lock(void);

/** Erases the flash page at given address. */
void flash_writer_page_erase(void *page);

/** Writes data to given location in flash. */
void flash_writer_page_write(void *page, uint8_t *data, size_t len);

#endif /* FLASH_WRITER_H */
