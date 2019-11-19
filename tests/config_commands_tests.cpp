#include <cstring>
#include <CppUTest/TestHarness.h>
#include <CppUTestExt/MockSupport.h>
#include <cmp_mem_access/cmp_mem_access.h>

#include "../flash_writer.h"
#include "../command.h"
#include "mocks/platform_mock.h"

TEST_GROUP (ConfigCommandTestGroup) {
    cmp_mem_access_t write_cma;
    cmp_mem_access_t read_cma;
    cmp_ctx_t write_ctx;
    cmp_ctx_t read_ctx;
    char data[1024];
    char out_data[1024];
    bootloader_config_t config;

    void setup()
    {
        cmp_mem_access_init(&write_ctx, &write_cma, data, sizeof data);
        cmp_mem_access_init(&read_ctx, &read_cma, out_data, sizeof out_data);
        memset(data, 0, sizeof data);
        memset(out_data, 0, sizeof out_data);
        memset(&config, 0, sizeof config);
    }
};

TEST(ConfigCommandTestGroup, CanChangeNodeID)
{
    cmp_write_map(&write_ctx, 1);

    cmp_write_str(&write_ctx, "ID", 2);
    cmp_write_u8(&write_ctx, 42);

    cmp_mem_access_set_pos(&write_cma, 0);

    command_config_update(1, &write_ctx, &read_ctx, &config);

    CHECK_EQUAL(42, config.ID);

    // check return value
    bool ret = false;
    cmp_mem_access_set_pos(&read_cma, 0);
    cmp_read_bool(&read_ctx, &ret);
    CHECK_TRUE(ret);
}

TEST(ConfigCommandTestGroup, CanReadConfig)
{
    bootloader_config_t read_config;
    memset(&read_config, 0, sizeof(read_config));

    config.ID = 42;
    command_config_read(0, NULL, &write_ctx, &config);

    cmp_mem_access_set_pos(&write_cma, 0);

    config_update_from_serialized(&read_config, &write_ctx);

    // Just check that the first field matches.
    // The rest is tested in ConfigSerializationTest
    CHECK_EQUAL(config.ID, read_config.ID);
}
