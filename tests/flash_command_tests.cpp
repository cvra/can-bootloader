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

    void setup()
    {
        serializer_init(&serializer, command_data, sizeof command_data);
        serializer_cmp_ctx_factory(&command_builder, &serializer);
        memset(command_data, 0, sizeof command_data);
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
    cmp_write_uint(&command_builder, (size_t)page);
    cmp_write_ext(&command_builder, 0x00, strlen(data), data);

    mock("flash").expectOneCall("unlock");
    mock("flash").expectOneCall("lock");
    mock("flash").expectOneCall("page_erase").withPointerParameter("adress", page);

    mock("flash").expectOneCall("page_write")
                 .withPointerParameter("page_adress", page)
                 .withIntParameter("size", strlen(data));

    command_write_flash(1, &command_builder, NULL);

    STRCMP_EQUAL(data, page);
}

TEST(FlashCommandTestGroup, CheckErrorHandlingWithIllFormatedArguments)
{
    // We simply check that no mock flash operation occurs
    command_write_flash(1, &command_builder, NULL);
}
