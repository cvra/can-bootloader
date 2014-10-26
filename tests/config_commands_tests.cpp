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
    bootloader_config_t config;

    void setup()
    {
        serializer_init(&serializer, command_data, sizeof command_data);
        serializer_cmp_ctx_factory(&command_builder, &serializer);
        memset(command_data, 0, sizeof command_data);
        memset(&config, 0, sizeof config);
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
