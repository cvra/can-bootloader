#include "CppUTest/TestHarness.h"
#include "CppUTestExt/MockSupport.h"

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
                 .withPointerParameter("source_adress", page1)
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
                 .withPointerParameter("source_adress", page2)
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
