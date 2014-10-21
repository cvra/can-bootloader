#include <serializer/checksum_block.h>
#include "flash_writer.h"
#include "config.h"

void config_sync_pages(void *page1, void *page2, size_t page_size)
{
    if (!config_is_valid(page1, page_size)) {
        flash_writer_page_erase(page1);
        flash_writer_page_write(page1, page2, page_size);
    }

    if (!config_is_valid(page2, page_size)) {
        flash_writer_page_erase(page2);
        flash_writer_page_write(page2, page1, page_size);
    }
}

bool config_is_valid(void *page, size_t page_size)
{
    return block_crc_verify(page, page_size);
}
