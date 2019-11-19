#include <string.h>
#include <cmp_mem_access/cmp_mem_access.h>
#include <crc/crc32.h>
#include "config.h"

static uint32_t config_calculate_crc(void* page, size_t page_size)
{
    return crc32(0, (uint8_t*)page + 4, page_size - 4);
}

bool config_is_valid(void* page, size_t page_size)
{
    uint32_t crc = 0;
    uint8_t* p = page;
    crc |= p[0] << 24;
    crc |= p[1] << 16;
    crc |= p[2] << 8;
    crc |= p[3] << 0;
    return crc == config_calculate_crc(page, page_size);
}

void config_write(void* buffer, bootloader_config_t* config, size_t buffer_size)
{
    cmp_ctx_t context;
    cmp_mem_access_t cma;
    uint8_t* p = buffer;

    cmp_mem_access_init(&context, &cma, &p[4], buffer_size - 4);
    config_write_messagepack(&context, config);

    uint32_t crc = config_calculate_crc(buffer, buffer_size);
    p[0] = ((crc >> 24) & 0xff);
    p[1] = ((crc >> 16) & 0xff);
    p[2] = ((crc >> 8) & 0xff);
    p[3] = (crc & 0xff);
}

void config_write_messagepack(cmp_ctx_t* context, bootloader_config_t* config)
{
    cmp_write_map(context, 6);

    cmp_write_str(context, "ID", 2);
    cmp_write_u8(context, config->ID);

    cmp_write_str(context, "name", 4);
    cmp_write_str(context, config->board_name, strlen(config->board_name));

    cmp_write_str(context, "device_class", 12);
    cmp_write_str(context, config->device_class, strlen(config->device_class));

    cmp_write_str(context, "application_crc", 15);
    cmp_write_uint(context, config->application_crc);

    cmp_write_str(context, "application_size", 16);
    cmp_write_uint(context, config->application_size);

    cmp_write_str(context, "update_count", 12);
    cmp_write_uint(context, config->update_count);
}

bootloader_config_t config_read(void* buffer, size_t buffer_size)
{
    bootloader_config_t result;

    cmp_ctx_t context;
    cmp_mem_access_t cma;

    cmp_mem_access_ro_init(&context, &cma, (uint8_t*)buffer + 4, buffer_size - 4);
    config_update_from_serialized(&result, &context);

    return result;
}

void config_update_from_serialized(bootloader_config_t* config, cmp_ctx_t* context)
{
    uint32_t key_count = 0;
    char key[64];
    uint32_t key_len;

    cmp_read_map(context, &key_count);

    while (key_count--) {
        key_len = sizeof key;
        cmp_read_str(context, key, &key_len);
        key[key_len] = 0;

        if (!strcmp("ID", key)) {
            cmp_read_uchar(context, &config->ID);
        }

        if (!strcmp("name", key)) {
            uint32_t name_len = 65;
            cmp_read_str(context, config->board_name, &name_len);
        }

        if (!strcmp("device_class", key)) {
            uint32_t name_len = 65;
            cmp_read_str(context, config->device_class, &name_len);
        }

        if (!strcmp("application_crc", key)) {
            cmp_read_uint(context, &config->application_crc);
        }

        if (!strcmp("application_size", key)) {
            cmp_read_uint(context, &config->application_size);
        }

        if (!strcmp("update_count", key)) {
            cmp_read_uint(context, &config->update_count);
        }
    }
}
