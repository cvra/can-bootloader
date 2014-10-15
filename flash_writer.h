
#ifndef FLASH_WRITER_H
#define FLASH_WRITER_H

#include <stdint.h>
#include <stddef.h>

/** Unlocks the flash for programming. */
void flash_writer_unlock(void);

/** Locks the flash */
void flash_writer_lock(void);

/** Returns the number of available pages. */
uint16_t flash_writer_num_pages(void);

/** Get info about start address and size of a page.
 * Returns false if page does not exist
 */
bool flash_writer_page_info(uint16_t page, void **addr, size_t *size);

/** Returns flash page size, 0 if page does not exist. */
size_t flash_writer_page_size(uint16_t page);

/** Returns address of flash page. */
void *flash_writer_page_address(uint16_t page);

/** Erases a whole page. */
void flash_writer_page_erase(uint16_t page);

/** Writes a word to erased page.
 * The address must be word aligned.
 * Returns 0 if the write operation was successful.
 */
int flash_writer_word_write(void *address, uint32_t word);

/** Writes a whole page, data size must be equal to the page size.
 * Verifying the written data is left to the application.
 */
void flash_writer_page_write(uint16_t page, uint8_t *data);

#endif /* FLASH_WRITER_H */
