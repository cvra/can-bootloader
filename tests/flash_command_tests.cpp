#include <cstring>
#include <CppUTest/TestHarness.h>
#include <CppUTestExt/MockSupport.h>
#include <crc/crc32.h>
#include <cmp_mem_access/cmp_mem_access.h>
#include "mocks/platform_mock.h"
#include "../flash_writer.h"
#include "../command.h"
#include "../boot_arg.h"

TEST_GROUP (FlashCommandTestGroup) {
    cmp_mem_access_t command_cma;
    cmp_ctx_t command_builder;
    char command_data[1024];
    bootloader_config_t config;

    cmp_ctx_t out;
    char out_data[1024];
    cmp_mem_access_t out_cma;

    void setup()
    {
        cmp_mem_access_init(&command_builder, &command_cma, command_data, sizeof command_data);
        memset(command_data, 0, sizeof command_data);

        cmp_mem_access_init(&out, &out_cma, out_data, sizeof out_data);
        memset(out_data, 0, sizeof out_data);

        // Creates a dummy device class for testing
        strcpy(config.device_class, "test.dummy");

        // Erases flash memory
        memset(memory_mock_app, 0, sizeof(memory_mock_app));
    }

    void teardown()
    {
        mock().checkExpectations();
        mock().clear();
    }
};

TEST(FlashCommandTestGroup, CanFlashSinglePage)
{
    const char* data = "xkcd";

    // Writes the adress of the page
    cmp_write_u64(&command_builder, (size_t)memory_mock_app);

    // Writes the correct device class
    cmp_write_str(&command_builder, config.device_class, strlen(config.device_class));

    cmp_write_bin(&command_builder, data, strlen(data));

    mock("flash").expectOneCall("unlock");
    mock("flash").expectOneCall("lock");

    mock("flash").expectOneCall("page_write").withPointerParameter("page_adress", memory_mock_app).withIntParameter("size", strlen(data));

    cmp_mem_access_set_pos(&command_cma, 0);
    command_write_flash(1, &command_builder, &out, &config);

    mock().checkExpectations();
    STRCMP_EQUAL(data, (char*)memory_mock_app);

    // check return value
    bool ret = false;
    cmp_mem_access_set_pos(&out_cma, 0);
    cmp_read_bool(&out, &ret);
    CHECK_TRUE(ret);
}

TEST(FlashCommandTestGroup, CheckErrorHandlingWithIllFormatedArguments)
{
    // We simply check that no mock flash operation occurs
    command_write_flash(1, &command_builder, &out, &config);

    mock().checkExpectations();

    // check return value
    bool ret = true;
    cmp_mem_access_set_pos(&out_cma, 0);
    cmp_read_bool(&out, &ret);
    CHECK_FALSE(ret);
}

TEST(FlashCommandTestGroup, CheckThatDeviceClassIsRespected)
{
    const char* data = "xkcd";

    // Writes the adress of the page
    cmp_write_uint(&command_builder, (size_t)memory_mock_app);

    // Writes a "wrong" device class
    cmp_write_str(&command_builder, "fail", 4);

    cmp_write_bin(&command_builder, data, strlen(data));

    cmp_mem_access_set_pos(&command_cma, 0);

    // Executes the command. Since the device class mismatch it should not make
    // any write
    command_write_flash(1, &command_builder, &out, &config);

    mock().checkExpectations();

    // check return value
    bool ret = true;
    cmp_mem_access_set_pos(&out_cma, 0);
    cmp_read_bool(&out, &ret);
    CHECK_FALSE(ret);
}

TEST(FlashCommandTestGroup, DoNotWritePastEndOfFlash)
{
    const char* data = "xkcd";

    // Try to write immediately after the end of the flash
    size_t past_end = (size_t)(&memory_mock_app[sizeof(memory_mock_app)]);
    cmp_write_u64(&command_builder, past_end);

    // Writes the correct device class
    cmp_write_str(&command_builder, config.device_class, strlen(config.device_class));

    // Write some data
    cmp_write_bin(&command_builder, data, strlen(data));

    // Execute the write flash command
    cmp_mem_access_set_pos(&command_cma, 0);
    command_write_flash(1, &command_builder, &out, &config);

    // No flash operation should have occured
    mock().checkExpectations();

    // An error should be returned
    bool ret;
    cmp_mem_access_set_pos(&out_cma, 0);
    CHECK_TRUE(cmp_read_bool(&out, &ret));
    CHECK_FALSE(ret);
}

TEST(FlashCommandTestGroup, CanErasePage)
{
    // Writes the adress of the page
    cmp_write_u64(&command_builder, (size_t)memory_mock_app);

    // Writes the correct device class
    cmp_write_str(&command_builder, config.device_class, strlen(config.device_class));

    mock("flash").expectOneCall("unlock");
    mock("flash").expectOneCall("lock");

    mock("flash").expectOneCall("page_erase").withPointerParameter("adress", memory_mock_app);

    cmp_mem_access_set_pos(&command_cma, 0);
    command_erase_flash_page(1, &command_builder, &out, &config);

    mock().checkExpectations();

    // check return value
    bool ret;
    cmp_mem_access_set_pos(&out_cma, 0);
    CHECK_TRUE(cmp_read_bool(&out, &ret));
    CHECK_TRUE(ret);
}

TEST(FlashCommandTestGroup, DeviceClassIsRespectedForErasePage)
{
    // Writes the adress of the page
    cmp_write_u64(&command_builder, (size_t)memory_mock_app);

    // Writes the wrong device class
    cmp_write_str(&command_builder, "fail", 4);

    cmp_mem_access_set_pos(&command_cma, 0);
    command_erase_flash_page(1, &command_builder, &out, &config);

    mock().checkExpectations();

    // check return value
    bool ret = true;
    cmp_mem_access_set_pos(&out_cma, 0);
    cmp_read_bool(&out, &ret);
    CHECK_FALSE(ret);
}

TEST(FlashCommandTestGroup, CheckIllFormatedArgumentsForErasePage)
{
    command_erase_flash_page(1, &command_builder, &out, &config);

    mock().checkExpectations();

    // check return value
    bool ret = true;
    cmp_mem_access_set_pos(&out_cma, 0);
    cmp_read_bool(&out, &ret);
    CHECK_FALSE(ret);
}

TEST(FlashCommandTestGroup, DoesNotErasePastEndOfFlash)
{
    // Try to erase immediately after the end of the flash
    size_t past_end = (size_t)(&memory_mock_app[sizeof(memory_mock_app)]);

    cmp_write_u64(&command_builder, past_end);

    // Writes the correct device class
    cmp_write_str(&command_builder, config.device_class, strlen(config.device_class));

    // Execute the command
    cmp_mem_access_set_pos(&command_cma, 0);
    command_erase_flash_page(1, &command_builder, &out, &config);

    // No flash operation should have occured
    mock().checkExpectations();

    // The operation should have failed
    bool ret = false;
    cmp_mem_access_set_pos(&out_cma, 0);
    CHECK_TRUE(cmp_read_bool(&out, &ret))
    CHECK_FALSE(ret);
}

TEST_GROUP (JumpToApplicationCodetestGroup) {
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

TEST_GROUP (ReadFlashTestGroup) {
    cmp_mem_access_t command_cma;
    cmp_ctx_t command_builder;
    char command_data[1024];

    cmp_mem_access_t output_cma;
    cmp_ctx_t output_builder;
    char output_data[1024];

    void setup(void)
    {
        cmp_mem_access_init(&command_builder, &command_cma, command_data, sizeof command_data);
        memset(command_data, 0, sizeof command_data);

        cmp_mem_access_init(&output_builder, &output_cma, output_data, sizeof output_data);
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

    cmp_mem_access_set_pos(&command_cma, 0);
    command_crc_region(0, &command_builder, &output_builder, NULL);

    cmp_mem_access_set_pos(&output_cma, 0);
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

    cmp_mem_access_set_pos(&command_cma, 0);
    command_read_flash(2, &command_builder, &output_builder, NULL);

    cmp_mem_access_set_pos(&output_cma, 0);
    cmp_read_bin(&output_builder, read_data, &read_size);

    CHECK_EQUAL(strlen(page), read_size);

    // Null terminate the string
    read_data[read_size] = '\0';
    STRCMP_EQUAL(page, read_data);
}

TEST_GROUP (PingTestGroup) {
    cmp_mem_access_t output_cma;
    cmp_ctx_t output_builder;
    char output_data[1024];

    void setup(void)
    {
        cmp_mem_access_init(&output_builder, &output_cma, output_data, sizeof output_data);
        memset(output_data, 0, sizeof output_data);
    }
};

TEST(PingTestGroup, PingCommand)
{
    bool result, success;
    command_ping(0, NULL, &output_builder, NULL);
    cmp_mem_access_set_pos(&output_cma, 0);
    success = cmp_read_bool(&output_builder, &result);

    CHECK_TRUE(success);
    CHECK_TRUE(result);
}
