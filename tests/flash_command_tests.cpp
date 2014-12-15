#include <cstring>
#include <CppUTest/TestHarness.h>
#include <CppUTestExt/MockSupport.h>
#include <serializer/serialization.h>
#include "../flash_writer.h"
#include "../command.h"


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
    mock("flash").expectOneCall("page_erase").withPointerParameter("adress", page);

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
}

TEST(FlashCommandTestGroup, CheckThatDeviceClassIsRespected)
{
    const char *data = "xkcd";

    // Writes the adress of the page
    cmp_write_uint(&command_builder, (size_t)page);

    // Writes a "wrong" device class
    cmp_write_str(&command_builder, "fail", 4);

    cmp_write_ext(&command_builder, 0x00, strlen(data), data);

    // Executes the command. Since the device class mismatch it should not make
    // any write
    command_write_flash(1, &command_builder, NULL, &config);
}

TEST_GROUP(JumpToApplicationCodetestGroup)
{
};

static void main_mock(void)
{
    mock().actualCall("application");
}

TEST(JumpToApplicationCodetestGroup, CanJumpToApplication)
{
    extern void (*application_main)(void);
    UT_PTR_SET(application_main, main_mock);
    mock().expectOneCall("application");

    // We don't have any arguments and we won't write any datagram so we can safely pass NULL
    command_jump_to_application(0, NULL, NULL, NULL);

    mock().checkExpectations();
    mock().clear();
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
