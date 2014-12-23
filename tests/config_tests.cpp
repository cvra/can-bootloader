#include "CppUTest/TestHarness.h"
#include "CppUTestExt/MockSupport.h"

#include <cstring>

#include "../config.h"
#include <serializer/checksum_block.h>

TEST_GROUP(ConfigPage)
{
    static const int page_size = 30;
    char page1[page_size], page2[page_size];

    void teardown(void)
    {
        mock().checkExpectations();
        mock().clear();
    }
};

TEST(ConfigPage, WhenConfigCRCMatchesNoWriteOccurs)
{
    // Makes two valid CRC blocks
    block_crc_update(page1, page_size);
    block_crc_update(page2, page_size);

    // We don't expect any flash writes to occur

    config_sync_pages(page1, page2, page_size);
}

TEST(ConfigPage, FirstPageIsCopiedIntoSecond)
{
    mock("flash").expectOneCall("page_write")
                 .withPointerParameter("page_adress", page2)
                 .withIntParameter("size", page_size);

    mock("flash").expectOneCall("page_erase")
                 .withPointerParameter("adress", page2);

    // Mark first page as valid
    block_crc_update(page1, page_size);

    config_sync_pages(page1, page2, page_size);
}

TEST(ConfigPage, SecondPageIsCopiedIntoFirst)
{
    mock("flash").expectOneCall("page_write")
                 .withPointerParameter("page_adress", page1)
                 .withIntParameter("size", page_size);

    mock("flash").expectOneCall("page_erase")
                 .withPointerParameter("adress", page1);

    // Mark second page as valid
    block_crc_update(page2, page_size);

    config_sync_pages(page1, page2, page_size);
}

TEST(ConfigPage, ConfigIsInvalid)
{
    CHECK_FALSE(config_is_valid(page1, page_size));
}

TEST(ConfigPage, ConfigIsValid)
{
    block_crc_update(page1, page_size);
    CHECK_TRUE(config_is_valid(page1, page_size));
}

TEST_GROUP(ConfigSerializationTest)
{
    char config_buffer[1024];
    bootloader_config_t config, result;

    void setup(void)
    {
        memset(config_buffer, 0, sizeof(config_buffer));
        memset(&config, 0,  sizeof (bootloader_config_t));
        memset(&result, 0,  sizeof (bootloader_config_t));
    }

    void config_read_and_write()
    {
        config_write(config_buffer, &config, sizeof config_buffer);
        result = config_read(config_buffer, sizeof config_buffer);
    }
};

TEST(ConfigSerializationTest, CanSerializeNodeID)
{
    config.ID = 0x12;

    config_read_and_write();

    CHECK_EQUAL(config.ID, result.ID);
}

TEST(ConfigSerializationTest, CanSerializeNodeName)
{
    strncpy(config.board_name, "test.dummy", 64);

    config_read_and_write();

    STRCMP_EQUAL(config.board_name, result.board_name);
}

TEST(ConfigSerializationTest, CanSerializeNodeDeviceClass)
{
    strncpy(config.device_class, "CVRA.dummy.v1", 64);

    config_read_and_write();

    STRCMP_EQUAL(config.device_class, result.device_class);
}

TEST(ConfigSerializationTest, CanSerializeApplicationCRC)
{
    config.application_crc = 0xdeadbeef;

    config_read_and_write();

    CHECK_EQUAL(0xdeadbeef, result.application_crc);
}

TEST(ConfigSerializationTest, CanSerializeApplicationSize)
{
    config.application_size = 42;

    config_read_and_write();

    CHECK_EQUAL(42, result.application_size);
}

TEST(ConfigSerializationTest, CanSerializeUpdateCount)
{
    config.update_count = 23;

    config_read_and_write();

    CHECK_EQUAL(23, result.update_count);
}
