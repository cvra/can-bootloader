#include <cstring>
#include <CppUTest/TestHarness.h>
#include <CppUTestExt/MockSupport.h>
#include <serializer/serialization.h>
#include <crc/crc32.h>
#include "mocks/memory_mock.h"
#include "../flash_writer.h"
#include "../command.h"
#include "../boot_arg.h"


TEST_GROUP(FlashCommandTestGroup)
{
    serializer_t serializer;
    cmp_ctx_t command_builder;
    char command_data[1024];
    char page[1024];
    bootloader_config_t config;

    void setup()
    {
        serializer_init(&serializer, command_data, sizeof command_data);
        serializer_cmp_ctx_factory(&command_builder, &serializer);
        memset(command_data, 0, sizeof command_data);

        // Creates a dummy device class for testing
        strcpy(config.device_class, "test.dummy");
    }

    void teardown()
    {
        mock().checkExpectations();
        mock().clear();
    }
};

TEST(FlashCommandTestGroup, CanFlashSinglePage)
{
    const char *data = "xkcd";

    // Writes the adress of the page
    cmp_write_u64(&command_builder, (size_t)page);

    // Writes the correct device class
    cmp_write_str(&command_builder, config.device_class, strlen(config.device_class));

    cmp_write_bin(&command_builder, data, strlen(data));

    mock("flash").expectOneCall("unlock");
    mock("flash").expectOneCall("lock");

    mock("flash").expectOneCall("page_write")
                 .withPointerParameter("page_adress", page)
                 .withIntParameter("size", strlen(data));

    command_write_flash(1, &command_builder, NULL, &config);

    mock().checkExpectations();
    STRCMP_EQUAL(data, page);
}

TEST(FlashCommandTestGroup, CheckErrorHandlingWithIllFormatedArguments)
{
    // We simply check that no mock flash operation occurs
    command_write_flash(1, &command_builder, NULL, &config);

    mock().checkExpectations();
}

TEST(FlashCommandTestGroup, CheckThatDeviceClassIsRespected)
{
    const char *data = "xkcd";

    // Writes the adress of the page
    cmp_write_uint(&command_builder, (size_t)page);

    // Writes a "wrong" device class
    cmp_write_str(&command_builder, "fail", 4);

    cmp_write_bin(&command_builder, data, strlen(data));

    // Executes the command. Since the device class mismatch it should not make
    // any write
    command_write_flash(1, &command_builder, NULL, &config);

    mock().checkExpectations();
}

TEST(FlashCommandTestGroup, CanErasePage)
{
    int page;

    // Writes the adress of the page
    cmp_write_u64(&command_builder, (size_t)&page);

    // Writes the correct device class
    cmp_write_str(&command_builder, config.device_class, strlen(config.device_class));

    mock("flash").expectOneCall("unlock");
    mock("flash").expectOneCall("lock");

    mock("flash").expectOneCall("page_erase").withPointerParameter("adress", &page);

    command_erase_flash_page(1, &command_builder, NULL, &config);

    mock().checkExpectations();
}

TEST(FlashCommandTestGroup, DeviceClassIsRespectedForErasePage)
{
    // Writes the adress of the page
    cmp_write_u64(&command_builder, (size_t)&page);

    // Writes the correct device class
    cmp_write_str(&command_builder, "fail", 4);

    command_erase_flash_page(1, &command_builder, NULL, &config);

    mock().checkExpectations();
}

TEST(FlashCommandTestGroup, CheckIllFormatedArgumentsForErasePage)
{
    command_erase_flash_page(1, &command_builder, NULL, &config);

    mock().checkExpectations();
}

TEST_GROUP(JumpToApplicationCodetestGroup)
{
    bootloader_config_t config;
    void teardown()
    {
        mock().checkExpectations();
        mock().clear();
    }
};

TEST(JumpToApplicationCodetestGroup, CanJumpToApplication)
{
    // setup application data and run crc over it
    memset(&memory_mock_app[0], 0x2a, sizeof(memory_mock_app));

    config.application_size = sizeof(memory_mock_app);

    config.application_crc = crc32(0, &memory_mock_app[0], sizeof(memory_mock_app));

    // Expect to reboot into application
    mock().expectOneCall("reboot").withIntParameter("arg", BOOT_ARG_START_APPLICATION);

    command_jump_to_application(0, NULL, NULL, &config);
}

TEST(JumpToApplicationCodetestGroup, WrongCRCMeansReboot)
{
    // setup application data and run crc over it
    memset(&memory_mock_app[0], 0x2a, sizeof(memory_mock_app));

    config.application_size = sizeof(memory_mock_app);

    // ensure wrong application crc
    config.application_crc = 0xbad ^ crc32(0, &memory_mock_app[0], sizeof(memory_mock_app));

    // Expect to reboot into itself with timeout disabled
    mock().expectOneCall("reboot").withIntParameter("arg", BOOT_ARG_START_BOOTLOADER_NO_TIMEOUT);

    command_jump_to_application(0, NULL, NULL, &config);
}

TEST(JumpToApplicationCodetestGroup, InvalidCRCReturnsToBootloader)
{
}


TEST_GROUP(ReadFlashTestGroup)
{
    serializer_t command_serializer;
    cmp_ctx_t command_builder;
    char command_data[1024];

    serializer_t output_serializer;
    cmp_ctx_t output_builder;
    char output_data[1024];

    void setup(void)
    {
        serializer_init(&command_serializer, command_data, sizeof command_data);
        serializer_cmp_ctx_factory(&command_builder, &command_serializer);
        memset(command_data, 0, sizeof command_data);

        serializer_init(&output_serializer, output_data, sizeof output_data);
        serializer_cmp_ctx_factory(&output_builder, &output_serializer);
        memset(output_data, 0, sizeof output_data);
    }
};

TEST(ReadFlashTestGroup, CanGetCRCOfARegion)
{
    uint32_t crc;
    bool success;
    char page[32];

    memset(page, 0, sizeof page);

    // Writes adress
    cmp_write_u64(&command_builder, (size_t)page);

    // Writes length
    cmp_write_uint(&command_builder, sizeof page);

    command_crc_region(0, &command_builder, &output_builder, NULL);
    success = cmp_read_uint(&output_builder, &crc);
    CHECK_TRUE(success);
    CHECK_EQUAL(0x190a55ad, crc);
}

TEST(ReadFlashTestGroup, CanReadData)
{
    char page[] = "Hello, world";
    char read_data[128];
    uint32_t read_size = sizeof read_data;

    cmp_write_u64(&command_builder, (size_t)page);
    cmp_write_u32(&command_builder, strlen(page));

    command_read_flash(2, &command_builder, &output_builder, NULL);
    cmp_read_bin(&output_builder, read_data, &read_size);

    CHECK_EQUAL(strlen(page), read_size);

    // Null terminate the string
    read_data[read_size] = '\0';
    STRCMP_EQUAL(page, read_data);
}

TEST_GROUP(PingTestGroup)
{
    serializer_t output_serializer;
    cmp_ctx_t output_builder;
    char output_data[1024];

    void setup(void)
    {
        serializer_init(&output_serializer, output_data, sizeof output_data);
        serializer_cmp_ctx_factory(&output_builder, &output_serializer);
        memset(output_data, 0, sizeof output_data);
    }
};

TEST(PingTestGroup, PingCommand)
{
    bool result, success;
    command_ping(0, NULL, &output_builder, NULL);
    success = cmp_read_bool(&output_builder, &result);

    CHECK_TRUE(success);
    CHECK_TRUE(result);
}
