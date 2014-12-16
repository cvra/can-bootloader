#include <string.h>
#include <crc/crc32.h>
#include <serializer/checksum_block.h>
#include "flash_writer.h"
#include "boot_arg.h"
#include "config.h"
#include "command.h"

extern int app_start, config_page1, config_page2;   // defined by linker

// temporary, pagesize for stm32f3
uint8_t page_buffer[2048];

void command_write_flash(int argc, cmp_ctx_t *args, cmp_ctx_t *out, bootloader_config_t *config)
{
    void *address;
    void *src;
    uint64_t tmp;
    uint32_t size;
    char device_class[64];

    cmp_read_uinteger(args, &tmp);
    address = (void *)tmp;

    // refuse to overwrite bootloader or config pages
    if (address < &app_start) {
        return;
    }

    size = 64;
    cmp_read_str(args, device_class, &size);

    if (strcmp(device_class, config->device_class) != 0) {
        return;
    }

    if (!cmp_read_bin_size(args, &size)) {
        return;
    }

    /* This is ugly, yet required to achieve zero copy. */
    src = ((serializer_t *)(args->buf))->_read_cursor;

    flash_writer_unlock();

    flash_writer_page_erase(address);

    flash_writer_page_write(address, src, size);

    flash_writer_lock();
}

void command_read_flash(int argc, cmp_ctx_t *args, cmp_ctx_t *out, bootloader_config_t *config)
{
    void *address;
    uint64_t tmp;
    uint32_t size;

    cmp_read_uinteger(args, &tmp);
    address = (void *)tmp;

    cmp_read_u32(args, &size);

    cmp_write_bin(out, address, size);
}

void command_jump_to_application(int argc, cmp_ctx_t *args, cmp_ctx_t *out, bootloader_config_t *config)
{
    if (crc32(0, &app_start, config->application_size) == config->application_crc) {
        reboot(BOOT_ARG_START_APPLICATION);
    } else {
        reboot(BOOT_ARG_START_BOOTLOADER_NO_TIMEOUT);
    }
}

void command_crc_region(int argc, cmp_ctx_t *args, cmp_ctx_t *out, bootloader_config_t *config)
{
    uint32_t crc;
    void *address;
    uint32_t size;
    uint64_t tmp;

    cmp_read_uinteger(args, &tmp);
    address = (void *)tmp;
    cmp_read_uint(args, &size);

    crc = crc32(0, address, size);
    cmp_write_uint(out, crc);
}

void command_config_update(int argc, cmp_ctx_t *args, cmp_ctx_t *out, bootloader_config_t *config)
{
    config_update_from_serialized(config, args);
}

void command_config_write_to_flash(int argc, cmp_ctx_t *args, cmp_ctx_t *out, bootloader_config_t *config)
{
    config->update_count += 1;

    memset(page_buffer, 0, sizeof(page_buffer));

    config_write(page_buffer + 4, config, sizeof(page_buffer));
    block_crc_update(page_buffer, sizeof(page_buffer) - 4);

    flash_writer_unlock();
    flash_writer_page_erase(&config_page1);
    flash_writer_page_write(&config_page1, page_buffer, sizeof(page_buffer));
    flash_writer_lock();

    if (block_crc_verify(&config_page1, sizeof(page_buffer))) {
        flash_writer_unlock();
        flash_writer_page_erase(&config_page2);
        flash_writer_page_write(&config_page2, page_buffer, sizeof(page_buffer));
        flash_writer_lock();
    }
}

int protocol_execute_command(char *data, size_t data_len, command_t *commands, int command_len, char *out_buf, size_t out_len, bootloader_config_t *config)
{
    serializer_t serializer;
    cmp_ctx_t command_reader;
    int32_t commmand_index, i;
    uint32_t argc;
    bool read_success;

    serializer_t out_serializer;
    cmp_ctx_t out_writer;

    serializer_init(&serializer, data, data_len);
    serializer_cmp_ctx_factory(&command_reader, &serializer);

    serializer_init(&out_serializer, out_buf, out_len);
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
            commands[i].callback(argc, &command_reader, &out_writer, config);
            return serializer_written_bytes_count(&out_serializer);
        }
    }

    return -ERR_COMMAND_NOT_FOUND;
}
