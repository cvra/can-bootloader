#include "../../flash_writer.h"
#include "CppUTest/TestHarness.h"
#include "CppUTestExt/MockSupport.h"


void flash_writer_unlock(void)
{
    mock("flash").actualCall("unlock");
}

void flash_writer_lock(void)
{
    mock("flash").actualCall("lock");
}

void flash_writer_page_erase(void *adress)
{
    mock("flash").actualCall("page_erase")
                 .withPointerParameter("adress", adress);
}

void flash_writer_page_write(void *page, void *data, size_t len)
{
    mock("flash").actualCall("page_write")
                 .withPointerParameter("page_adress", page)
                 .withPointerParameter("source_adress", data)
                 .withIntParameter("size", len);
}

/* This TEST_GROUP contains the tests to check that the mock flash functions
 * are working properly. */
TEST_GROUP(FlashWriterMockTestGroup)
{
    void teardown()
    {
        mock().checkExpectations();
        mock().clear();
    }
};

TEST(FlashWriterMockTestGroup, CanUnlock)
{
    mock("flash").expectOneCall("unlock");
    flash_writer_unlock();
}

TEST(FlashWriterMockTestGroup, CanLock)
{
    mock("flash").expectOneCall("lock");
    flash_writer_lock();
}

TEST(FlashWriterMockTestGroup, CanErasePage)
{
    mock("flash").expectOneCall("page_erase")
                 .withPointerParameter("adress", (void *)0xdeadbeef);

    flash_writer_page_erase((void *)0xdeadbeef);
}

TEST(FlashWriterMockTestGroup, CanWritePage)
{
    mock("flash").expectOneCall("page_write")
                 .withPointerParameter("page_adress", (void *)0xcafebabe)
                 .withPointerParameter("source_adress", (void *)0xdeadbeef)
                 .withIntParameter("size", 42);

    flash_writer_page_write((void *)0xcafebabe, (void *)0xdeadbeef, 42);
}

