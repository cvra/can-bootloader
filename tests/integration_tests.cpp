#include <CppUTest/TestHarness.h>
#include <CppUTestExt/MockSupport.h>

#include "../can_datagram.h"
#include "../config.h"
#include "mocks/can_interface_mock.h"
#include "../can_interface.h"
#include "../command.h"
#include <cstdio>

void read_eval(can_datagram_t* input, can_datagram_t* output, bootloader_config_t* config, command_t* commands, int command_len)
{
    uint32_t message_id;
    uint8_t message[8];
    uint8_t len;
    int i;

    can_interface_read_message(&message_id, message, &len, 1);

    for (i = 0; i < len; ++i) {
        can_datagram_input_byte(input, message[i]);
    }

    // Bypass CRC check
    input->crc = can_datagram_compute_crc(input);

    if (can_datagram_is_valid(input)) {
        for (i = 0; i < input->destination_nodes_len; ++i) {
            if (input->destination_nodes[i] == config->ID) {
                len = protocol_execute_command((char*)input->data, input->data_len, commands, command_len, (char*)output->data, output->data_len, config);

                /* Checks if there was any error. */
                if (len < 0) {
                    return;
                }

                output->data_len = len;
            }
        }

        if (output->data_len > 0) {
            output->destination_nodes_len = 1;
            output->crc = can_datagram_compute_crc(output);
        }
    }
}

static void mock_command(int argc, cmp_ctx_t* arg_context, cmp_ctx_t* out_context, bootloader_config_t* config)
{
    mock().actualCall("command");
}

TEST_GROUP (IntegrationTesting) {
    can_datagram_t input_datagram;
    uint8_t input_datagram_destinations[10];
    uint8_t input_datagram_data[1000];

    can_datagram_t output_datagram;
    uint8_t output_datagram_destinations[10];
    uint8_t output_datagram_data[1000];

    bootloader_config_t config;
    command_t commands[1];

    void setup(void)
    {
        can_datagram_init(&input_datagram);
        can_datagram_set_address_buffer(&input_datagram, input_datagram_destinations);
        can_datagram_set_data_buffer(&input_datagram, input_datagram_data, sizeof input_datagram_data);

        can_datagram_init(&output_datagram);
        can_datagram_set_address_buffer(&output_datagram, output_datagram_destinations);
        can_datagram_set_data_buffer(&output_datagram, output_datagram_data, sizeof output_datagram_data);

        // Loads default config for testing
        config.ID = 0x01;

        commands[0].index = 1;
        commands[0].callback = mock_command;
    }

    void teardown(void)
    {
        mock().clear();
    }
};

TEST(IntegrationTesting, CanReadWholeDatagram)
{
    uint8_t message[] = {
        CAN_DATAGRAM_VERSION,
        0x00, 0x00, 0x00, 0x00, // CRC
        0x01,
        0x01, // dest nodes
        0x0, 0x0, 0x0, 0x1,
        0x1 // data
    };

    can_mock_message(0x0, &message[0], 8);
    read_eval(&input_datagram, &output_datagram, &config, NULL, 0);
    mock().checkExpectations();

    can_mock_message(0x0, &message[8], 4);
    read_eval(&input_datagram, &output_datagram, &config, NULL, 0);
    mock().checkExpectations();

    CHECK_TRUE(can_datagram_is_valid(&input_datagram));
}

TEST(IntegrationTesting, ExecutesCommand)
{
    uint8_t message[] = {
        CAN_DATAGRAM_VERSION,
        0x00, 0x00, 0x00, 0x00, // CRC
        0x01,
        0x01, // dest nodes
        0x0, 0x0, 0x0, 0x2,
        COMMAND_SET_VERSION, 0x1 // data
    };

    can_mock_message(0x0, &message[0], 8);
    read_eval(&input_datagram, &output_datagram, &config, commands, 1);
    mock().checkExpectations();

    can_mock_message(0x0, &message[8], 5);
    mock().expectOneCall("command");
    read_eval(&input_datagram, &output_datagram, &config, commands, 1);
    mock().checkExpectations();
}

TEST(IntegrationTesting, ExecutesIfWeAreInMultiCast)
{
    uint8_t message[] = {
        CAN_DATAGRAM_VERSION,
        0x00, 0x00, 0x00, 0x00, // CRC
        0x02,
        0x01, 0x12, // dest nodes
        0x0, 0x0, 0x0, 0x2,
        COMMAND_SET_VERSION, 0x1 // data
    };

    config.ID = 0x12;

    can_mock_message(0x0, &message[0], 8);
    read_eval(&input_datagram, &output_datagram, &config, commands, 1);
    mock().checkExpectations();

    can_mock_message(0x0, &message[8], 6);
    mock().expectOneCall("command");
    read_eval(&input_datagram, &output_datagram, &config, commands, 1);
    mock().checkExpectations();
}

static void command_output(int argc, cmp_ctx_t* arg_context, cmp_ctx_t* out_context, bootloader_config_t* config)
{
    cmp_write_str(out_context, "hello", 5);
}

TEST(IntegrationTesting, OutputDatagramIsValid)
{
    uint8_t message[] = {
        CAN_DATAGRAM_VERSION,
        0x00, 0x00, 0x00, 0x00, // CRC
        0x01,
        0x01, // dest nodes
        0x0, 0x0, 0x0, 0x2,
        COMMAND_SET_VERSION, 0x1 // data
    };

    commands[0].callback = command_output;

    can_mock_message(0x0, &message[0], 8);
    read_eval(&input_datagram, &output_datagram, &config, commands, 1);

    can_mock_message(0x0, &message[8], 5);
    read_eval(&input_datagram, &output_datagram, &config, commands, 1);

    // Check that the data lenght is correct
    CHECK_EQUAL(6, output_datagram.data_len);
    CHECK_TRUE(can_datagram_is_valid(&output_datagram));
}
