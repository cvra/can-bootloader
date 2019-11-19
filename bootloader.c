#include <stdint.h>
#include <string.h>

#include <platform.h>
#include "command.h"
#include "can_datagram.h"
#include "config.h"
#include "boot_arg.h"
#include "timeout.h"
#include "can_interface.h"
#include "flash_writer.h"

#define BUFFER_SIZE FLASH_PAGE_SIZE + 128
#define DEFAULT_ID 0x01
#define CAN_SEND_RETRIES 100
#define CAN_RECEIVE_TIMEOUT 1000

uint8_t output_buf[BUFFER_SIZE];
uint8_t data_buf[BUFFER_SIZE];
uint8_t addr_buf[128];

const command_t commands[] = {
    {.index = 1, .callback = command_jump_to_application},
    {.index = 2, .callback = command_crc_region},
    {.index = 3, .callback = command_erase_flash_page},
    {.index = 4, .callback = command_write_flash},
    {.index = 5, .callback = command_ping},
    {.index = 6, .callback = command_read_flash},
    {.index = 7, .callback = command_config_update},
    {.index = 8, .callback = command_config_write_to_flash},
    {.index = 9, .callback = command_config_read}};

static void return_datagram(uint8_t source_id, uint8_t dest_id, uint8_t* data, size_t len)
{
    can_datagram_t dt;
    uint8_t dest_nodes[1];
    uint8_t buf[8];

    can_datagram_init(&dt);
    can_datagram_set_address_buffer(&dt, dest_nodes);
    can_datagram_set_data_buffer(&dt, data, len);
    dt.destination_nodes[0] = dest_id;
    dt.destination_nodes_len = 1;
    dt.data_len = len;
    dt.crc = can_datagram_compute_crc(&dt);

    bool start_of_datagram = true;
    while (true) {
        uint8_t dlc = can_datagram_output_bytes(&dt, (char*)buf, sizeof(buf));

        if (dlc == 0) {
            break;
        }

        if (start_of_datagram) {
            if (!can_interface_send_message(source_id | ID_START_MASK, buf, dlc,
                                            CAN_SEND_RETRIES)) {
                break; // failed
            }
            start_of_datagram = false;
        } else {
            if (!can_interface_send_message(source_id, buf, dlc, CAN_SEND_RETRIES)) {
                break; // failed
            }
        }
    }
}

void bootloader_main(int arg)
{
    bool timeout_active = !(arg == BOOT_ARG_START_BOOTLOADER_NO_TIMEOUT);

    flash_init();

    bootloader_config_t config;
    if (config_is_valid(memory_get_config1_addr(), CONFIG_PAGE_SIZE)) {
        config = config_read(memory_get_config1_addr(), CONFIG_PAGE_SIZE);
    } else if (config_is_valid(memory_get_config2_addr(), CONFIG_PAGE_SIZE)) {
        config = config_read(memory_get_config2_addr(), CONFIG_PAGE_SIZE);
    } else {
        // exact behaviour at invalid config is not yet defined.
        strcpy(config.device_class, PLATFORM_DEVICE_CLASS);
        strcpy(config.board_name, "foobar2000");
        config.ID = DEFAULT_ID;
        config.application_crc = 0xDEADC0DE;
        config.application_size = 0;
        config.update_count = 1;
    }

    can_datagram_t dt;
    can_datagram_init(&dt);
    can_datagram_set_address_buffer(&dt, addr_buf);
    can_datagram_set_data_buffer(&dt, data_buf, sizeof(data_buf));
    can_datagram_start(&dt);

    uint8_t data[8];
    uint32_t id;
    uint8_t len;
    while (true) {
        if (timeout_active && timeout_reached()) {
            command_jump_to_application(0, NULL, NULL, &config);
        }

        if (!can_interface_read_message(&id, data, &len, CAN_RECEIVE_TIMEOUT)) {
            continue;
        }

        if ((id & ID_START_MASK) != 0) {
            can_datagram_start(&dt);
        }

        int i;
        for (i = 0; i < len; i++) {
            can_datagram_input_byte(&dt, data[i]);
        }

        if (can_datagram_is_complete(&dt)) {
            if (can_datagram_is_valid(&dt)) {
                timeout_active = false;
                int i;
                for (i = 0; i < dt.destination_nodes_len; i++) {
                    if (dt.destination_nodes[i] == config.ID) {
                        timeout_active = false;
                        break;
                    }
                }
                if (i != dt.destination_nodes_len) {
                    // we were addressed
                    len = protocol_execute_command((char*)dt.data, dt.data_len,
                                                   &commands[0], sizeof(commands) / sizeof(command_t),
                                                   (char*)output_buf, sizeof(output_buf), &config);

                    if (len > 0) {
                        uint8_t return_id = id & ~ID_START_MASK;
                        return_datagram(config.ID, return_id, output_buf, (size_t)len);
                    }
                }
            }
            can_datagram_start(&dt);
        }
    }
}
