#include "command.h"
#include "flash_writer.h"
#include <string.h>
#include <crc/crc32.h>

// XXX Change page size
static char page_buffer[1024];

void (*application_main)(void);

void command_write_flash(int argc, cmp_ctx_t *args, cmp_ctx_t *out, bootloader_config_t *config)
{
    void *address;
    uint64_t tmp;

    int8_t type;
    int size;
    char device_class[64];

    bool success;

    cmp_read_u64(args, &tmp);
    address = (void *)tmp;

    size = 64;
    cmp_read_str(args, device_class, &size);

    if (strcmp(device_class, config->device_class) != 0) {
        return;
    }

    success = cmp_read_bin(args, page_buffer, &size);

    if (!success) {
        return;
    }

    flash_writer_unlock();

    flash_writer_page_erase(address);

    flash_writer_page_write(address, page_buffer, size);

    flash_writer_lock();
}

void command_jump_to_application(int argc, cmp_ctx_t *args, cmp_ctx_t *out, bootloader_config_t *config)
{
    application_main();
}

void command_crc_region(int argc, cmp_ctx_t *args, cmp_ctx_t *out, bootloader_config_t *config)
{
    uint32_t crc;
    void *address;
    uint32_t size;
    uint64_t tmp;

    cmp_read_u64(args, &tmp);
    address = (void *)tmp;
    cmp_read_uint(args, &size);

    crc = crc32(0, address, size);
    cmp_write_uint(out, crc);
}

void command_config_update(int argc, cmp_ctx_t *args, cmp_ctx_t *out, bootloader_config_t *config)
{
    config_update_from_serialized(config, args);
}

int protocol_execute_command(char *data, command_t *commands, int command_len, char *output_buffer, bootloader_config_t *config)
{
    serializer_t serializer;
    cmp_ctx_t command_reader;
    int commmand_index, i;
    int argc;
    bool read_success;

    serializer_t out_serializer;
    cmp_ctx_t out_writer;

    // XXX size 0 should be replaced with correct size
    serializer_init(&serializer, data, 0);
    serializer_cmp_ctx_factory(&command_reader, &serializer);

    serializer_init(&out_serializer, output_buffer, 0);
    serializer_cmp_ctx_factory(&out_writer, &out_serializer);

    read_success = cmp_read_int(&command_reader, &commmand_index);

    if (!read_success) {
        return -ERR_INVALID_COMMAND;
    }

    read_success = cmp_read_array(&command_reader, &argc);

    /* If we cannot read array size, assume it is because we don't have
     * arguments. */
    if (!read_success) {
        argc = 0;
    }

    for (i = 0; i < command_len; ++i) {
        if (commands[i].index == commmand_index) {
            commands[i].callback(argc, &command_reader, &out_writer, NULL);
            return serializer_written_bytes_count(&out_serializer);
        }
    }

    return -ERR_COMMAND_NOT_FOUND;
}
