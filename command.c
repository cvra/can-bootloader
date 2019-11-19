#include <string.h>
#include <crc/crc32.h>
#include <cmp_mem_access/cmp_mem_access.h>
#include <platform.h>
#include "flash_writer.h"
#include "boot_arg.h"
#include "config.h"
#include "command.h"

void command_erase_flash_page(int argc, cmp_ctx_t* args, cmp_ctx_t* out, bootloader_config_t* config)
{
    void* address;
    uint64_t tmp = 0;
    char device_class[64];

    cmp_read_uinteger(args, &tmp);
    address = (void*)(uintptr_t)tmp;

    // refuse to overwrite bootloader or config pages
    if (address < memory_get_app_addr()) {
        goto command_fail;
    }

    // Refuse to erase past end of flash memory
    if (address >= memory_get_app_addr() + memory_get_app_size()) {
        goto command_fail;
    }

    uint32_t size = 64;
    cmp_read_str(args, device_class, &size);

    if (strcmp(device_class, config->device_class) != 0) {
        goto command_fail;
    }

    flash_writer_unlock();

    flash_writer_page_erase(address);

    flash_writer_lock();

    cmp_write_bool(out, 1);
    return;

command_fail:
    cmp_write_bool(out, 0);
    return;
}

void command_write_flash(int argc, cmp_ctx_t* args, cmp_ctx_t* out, bootloader_config_t* config)
{
    void* address;
    void* src;
    uint64_t tmp = 0;
    uint32_t size;
    char device_class[64];

    cmp_read_uinteger(args, &tmp);
    address = (void*)(uintptr_t)tmp;

    // refuse to overwrite bootloader or config pages
    if (address < memory_get_app_addr()) {
        goto command_fail;
    }

    // Refuse to erase past end of flash memory
    if (address >= memory_get_app_addr() + memory_get_app_size()) {
        goto command_fail;
    }

    size = 64;
    cmp_read_str(args, device_class, &size);

    if (strcmp(device_class, config->device_class) != 0) {
        goto command_fail;
    }

    if (!cmp_read_bin_size(args, &size)) {
        goto command_fail;
    }

    /* This is ugly, yet required to achieve zero copy. */
    cmp_mem_access_t* cma = (cmp_mem_access_t*)(args->buf);
    src = cmp_mem_access_get_ptr_at_pos(cma, cmp_mem_access_get_pos(cma));

    flash_writer_unlock();

    flash_writer_page_write(address, src, size);

    flash_writer_lock();

    cmp_write_bool(out, 1);
    return;

command_fail:
    cmp_write_bool(out, 0);
    return;
}

void command_read_flash(int argc, cmp_ctx_t* args, cmp_ctx_t* out, bootloader_config_t* config)
{
    void* address;
    uint64_t tmp;
    uint32_t size;

    cmp_read_uinteger(args, &tmp);
    address = (void*)(uintptr_t)tmp;

    cmp_read_u32(args, &size);

    cmp_write_bin(out, address, size);
}

void command_jump_to_application(int argc, cmp_ctx_t* args, cmp_ctx_t* out, bootloader_config_t* config)
{
    if (crc32(0, memory_get_app_addr(), config->application_size) == config->application_crc) {
        reboot_system(BOOT_ARG_START_APPLICATION);
    } else {
        reboot_system(BOOT_ARG_START_BOOTLOADER_NO_TIMEOUT);
    }
}

void command_crc_region(int argc, cmp_ctx_t* args, cmp_ctx_t* out, bootloader_config_t* config)
{
    uint32_t crc;
    void* address;
    uint32_t size;
    uint64_t tmp;

    cmp_read_uinteger(args, &tmp);
    address = (void*)(uintptr_t)tmp;
    cmp_read_uint(args, &size);

    crc = crc32(0, address, size);
    cmp_write_uint(out, crc);
}

void command_config_update(int argc, cmp_ctx_t* args, cmp_ctx_t* out, bootloader_config_t* config)
{
    config_update_from_serialized(config, args);
    cmp_write_bool(out, 1);
}

void command_ping(int argc, cmp_ctx_t* args, cmp_ctx_t* out, bootloader_config_t* config)
{
    cmp_write_bool(out, 1);
}

static bool flash_write_and_verify(void* addr, void* data, size_t len)
{
    flash_writer_unlock();
    flash_writer_page_erase(addr);
    flash_writer_page_write(addr, data, len);
    flash_writer_lock();
    return config_is_valid(addr, len);
}

void command_config_write_to_flash(int argc, cmp_ctx_t* args, cmp_ctx_t* out, bootloader_config_t* config)
{
    config->update_count += 1;

    memset(config_page_buffer, 0, CONFIG_PAGE_SIZE);

    config_write(config_page_buffer, config, CONFIG_PAGE_SIZE);

    void* config1 = memory_get_config1_addr();
    void* config2 = memory_get_config2_addr();

    bool success = false;
    if (config_is_valid(config2, CONFIG_PAGE_SIZE)) {
        if (flash_write_and_verify(config1, config_page_buffer, CONFIG_PAGE_SIZE)) {
            if (flash_write_and_verify(config2, config_page_buffer, CONFIG_PAGE_SIZE)) {
                success = true;
            }
        }
    } else if (config_is_valid(config1, CONFIG_PAGE_SIZE)) {
        if (flash_write_and_verify(config2, config_page_buffer, CONFIG_PAGE_SIZE)) {
            if (flash_write_and_verify(config1, config_page_buffer, CONFIG_PAGE_SIZE)) {
                success = true;
            }
        }
    } else {
        success = flash_write_and_verify(config1, config_page_buffer, CONFIG_PAGE_SIZE);
        success &= flash_write_and_verify(config2, config_page_buffer, CONFIG_PAGE_SIZE);
    }

    if (success) {
        cmp_write_bool(out, 1);
    } else {
        cmp_write_bool(out, 0);
    }
}

void command_config_read(int argc, cmp_ctx_t* args, cmp_ctx_t* out, bootloader_config_t* config)
{
    config_write_messagepack(out, config);
}

int protocol_execute_command(char* data, size_t data_len, const command_t* commands, int command_len, char* out_buf, size_t out_len, bootloader_config_t* config)
{
    cmp_mem_access_t command_cma;
    cmp_ctx_t command_reader;
    int32_t commmand_index, i;
    uint32_t argc;
    int32_t command_version;
    bool read_success;

    cmp_mem_access_t out_cma;
    cmp_ctx_t out_writer;

    cmp_mem_access_ro_init(&command_reader, &command_cma, data, data_len);

    cmp_mem_access_init(&out_writer, &out_cma, out_buf, out_len);

    cmp_read_int(&command_reader, &command_version);

    if (command_version != COMMAND_SET_VERSION) {
        return -ERR_INVALID_COMMAND_SET_VERSION;
    }

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
            return cmp_mem_access_get_pos(&out_cma);
        }
    }

    return -ERR_COMMAND_NOT_FOUND;
}
