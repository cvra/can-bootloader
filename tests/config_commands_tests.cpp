#include <cstring>
#include <CppUTest/TestHarness.h>
#include <CppUTestExt/MockSupport.h>
#include <serializer/serialization.h>

#include "../flash_writer.h"
#include "../command.h"


TEST_GROUP(ConfigCommandTestGroup)
{
    serializer_t serializer;
    cmp_ctx_t command_builder;
    char command_data[1024];

    serializer_t out_serializer;
    cmp_ctx_t output_ctx;
    char output_data[1024];

    bootloader_config_t config;

    void setup()
    {
        serializer_init(&serializer, command_data, sizeof command_data);
        serializer_cmp_ctx_factory(&command_builder, &serializer);
        memset(command_data, 0, sizeof command_data);
        memset(&config, 0, sizeof config);

        serializer_init(&out_serializer, output_data, sizeof output_data);
        serializer_cmp_ctx_factory(&output_ctx, &out_serializer);
        memset(output_data, 0, sizeof output_data);
    }
};

TEST(ConfigCommandTestGroup, CanChangeNodeID)
{
    cmp_write_map(&command_builder, 1);

    cmp_write_str(&command_builder, "ID", 2);
    cmp_write_u8(&command_builder, 42);

    command_config_update(1, &command_builder, NULL, &config);

    CHECK_EQUAL(42, config.ID);
}

TEST(ConfigCommandTestGroup, CanReadConfig)
{
    bootloader_config_t read_config;
    memset(&read_config, 0, sizeof(read_config));

    config.ID = 42;
    command_config_read(0, NULL, &output_ctx, &config);
    config_update_from_serialized(&read_config, &output_ctx);

    // Just check that the first field matches.
    // The rest is tested in ConfigSerializationTest
    CHECK_EQUAL(config.ID, read_config.ID);
}
