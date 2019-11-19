#include "CppUTest/TestHarness.h"
#include "CppUTestExt/MockSupport.h"
#include <cstring>
#include "../config.h"

TEST_GROUP (ConfigTest) {
    char config_buffer[1024];
    bootloader_config_t config, result;

    void setup(void)
    {
        memset(config_buffer, 0, sizeof(config_buffer));
        memset(&config, 0, sizeof(bootloader_config_t));
        memset(&result, 0, sizeof(bootloader_config_t));
    }

    void config_read_and_write()
    {
        config_write(config_buffer, &config, sizeof config_buffer);
        result = config_read(config_buffer, sizeof config_buffer);
    }
};

TEST(ConfigTest, WritesValidConfigCRC)
{
    config.ID = 0x42;

    config_write(config_buffer, &config, sizeof config_buffer);

    CHECK_TRUE(config_is_valid(config_buffer, sizeof(config_buffer)));
}

TEST(ConfigTest, DetectsCorruptedConfig)
{
    config.ID = 0x42;

    config_write(config_buffer, &config, sizeof config_buffer);

    config_buffer[42] ^= 0x2A;

    CHECK_FALSE(config_is_valid(config_buffer, sizeof(config_buffer)));
}

TEST(ConfigTest, CanSerializeNodeID)
{
    config.ID = 0x12;

    config_read_and_write();

    CHECK_EQUAL(config.ID, result.ID);
}

TEST(ConfigTest, CanSerializeNodeName)
{
    strncpy(config.board_name, "test.dummy", 64);

    config_read_and_write();

    STRCMP_EQUAL(config.board_name, result.board_name);
}

TEST(ConfigTest, CanSerializeNodeDeviceClass)
{
    strncpy(config.device_class, "CVRA.dummy.v1", 64);

    config_read_and_write();

    STRCMP_EQUAL(config.device_class, result.device_class);
}

TEST(ConfigTest, CanSerializeApplicationCRC)
{
    config.application_crc = 0xdeadbeef;

    config_read_and_write();

    CHECK_EQUAL(0xdeadbeef, result.application_crc);
}

TEST(ConfigTest, CanSerializeApplicationSize)
{
    config.application_size = 42;

    config_read_and_write();

    CHECK_EQUAL(42, result.application_size);
}

TEST(ConfigTest, CanSerializeUpdateCount)
{
    config.update_count = 23;

    config_read_and_write();

    CHECK_EQUAL(23, result.update_count);
}
