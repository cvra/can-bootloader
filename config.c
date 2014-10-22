#include <serializer/checksum_block.h>
#include <serializer/serialization.h>
#include <string.h>
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

void config_write(void *buffer,  bootloader_config_t config, size_t buffer_size)
{
    cmp_ctx_t context;
    serializer_t serializer;

    // Create a MessagePack instance in memory
    serializer_init(&serializer, block_payload_get(buffer), buffer_size - 4);
    serializer_cmp_ctx_factory(&context, &serializer);

    cmp_write_map(&context, 2);

    cmp_write_str(&context, "ID", 2);
    cmp_write_u8(&context, config.ID);

    cmp_write_str(&context, "name", 4);
    cmp_write_str(&context, config.board_name, strlen(config.board_name));
}

bootloader_config_t config_read(void *buffer, size_t buffer_size)
{
    bootloader_config_t result;

    cmp_ctx_t context;
    serializer_t serializer;

    int key_count;
    char key[64];
    int key_len;

    // Create a MessagePack instance in memory
    serializer_init(&serializer, block_payload_get(buffer), buffer_size - 4);
    serializer_cmp_ctx_factory(&context, &serializer);

    cmp_read_map(&context, &key_count);

    while (key_count --) {
        key_len = sizeof key;
        cmp_read_str(&context, key, &key_len);
        key[key_len] = 0;

        if (!strcmp("ID", key)) {
            cmp_read_u8(&context, &result.ID);
        }

        if (!strcmp("name", key)) {
            int name_len;
            cmp_read_str(&context, result.board_name, &name_len);
            result.board_name[name_len] = 0;
        }
    }

    return result;
}
