#include <cstring>
#include "../../flash_writer.h"
#include "CppUTest/TestHarness.h"
#include "CppUTestExt/MockSupport.h"

// This symbol is supposed to be provided by the linker
extern "C" {
int app_start;
}

void flash_init(void)
{
}

void flash_writer_unlock(void)
{
    mock("flash").actualCall("unlock");
}

void flash_writer_lock(void)
{
    mock("flash").actualCall("lock");
}

void flash_writer_page_erase(void* adress)
{
    mock("flash").actualCall("page_erase").withPointerParameter("adress", adress);
}

void flash_writer_page_write(void* page, void* data, size_t len)
{
    mock("flash").actualCall("page_write").withPointerParameter("page_adress", page).withIntParameter("size", len);

    memcpy(page, data, len);
}

/* This TEST_GROUP contains the tests to check that the mock flash functions
 * are working properly. */
TEST_GROUP (FlashWriterMockTestGroup) {
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
    mock("flash").expectOneCall("page_erase").withPointerParameter("adress", (void*)0xdeadbeef);

    flash_writer_page_erase((void*)0xdeadbeef);
}

TEST(FlashWriterMockTestGroup, CanWritePage)
{
    char buf[30];
    char data[] = "Hello";

    mock("flash").expectOneCall("page_write").withPointerParameter("page_adress", buf).withIntParameter("size", strlen(data) + 1);

    flash_writer_page_write(buf, data, strlen(data) + 1);

    STRCMP_EQUAL(data, buf);
}
