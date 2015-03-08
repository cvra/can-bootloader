#include <cstring>
#include <CppUTest/TestHarness.h>
#include <CppUTestExt/MockSupport.h>
#include <cmp_mem_access/cmp_mem_access.h>

#include "../flash_writer.h"
#include "../command.h"


TEST_GROUP(ConfigCommandTestGroup)
{
    cmp_mem_access_t write_cma;
    cmp_mem_access_t read_cma;
    cmp_ctx_t write_ctx;
    cmp_ctx_t read_ctx;
    char data[1024];
    bootloader_config_t config;

    void setup()
    {
        cmp_mem_access_init(&write_ctx, &write_cma, data, sizeof data);
        cmp_mem_access_ro_init(&read_ctx, &read_cma, data, sizeof data);
        memset(data, 0, sizeof data);
        memset(&config, 0, sizeof config);
    }
};

TEST(ConfigCommandTestGroup, CanChangeNodeID)
{
    cmp_write_map(&write_ctx, 1);

    cmp_write_str(&write_ctx, "ID", 2);
    cmp_write_u8(&write_ctx, 42);

    command_config_update(1, &read_ctx, NULL, &config);

    CHECK_EQUAL(42, config.ID);
}

TEST(ConfigCommandTestGroup, CanReadConfig)
{
    bootloader_config_t read_config;
    memset(&read_config, 0, sizeof(read_config));

    config.ID = 42;
    command_config_read(0, NULL, &write_ctx, &config);
    config_update_from_serialized(&read_config, &read_ctx);

    // Just check that the first field matches.
    // The rest is tested in ConfigSerializationTest
    CHECK_EQUAL(config.ID, read_config.ID);
}
