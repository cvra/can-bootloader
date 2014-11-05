#include "../../can_interface.h"
#include "CppUTest/TestHarness.h"
#include "CppUTestExt/MockSupport.h"

#include <cstring>

static uint32_t expected_id;
uint8_t expected_msg[8];


int can_interface_read_message(uint32_t *message_id, uint8_t *message)
{
    return mock("can").actualCall("read")
                      .withOutputParameter("id", message_id)
                      .withOutputParameter("message", message)
                      .returnIntValue();
}

void can_interface_send_message(uint32_t message_id, uint8_t *message, int len)
{
    mock("can").actualCall("write")
               .withIntParameter("len", len)
               .withIntParameter("id", message_id);
}

void can_mock_message(uint32_t message_id, uint8_t *msg, int message_len)
{
    expected_id = message_id;
    memcpy(expected_msg, msg, message_len);

    mock("can").expectOneCall("read")
               .withOutputParameterReturning("id", &expected_id, sizeof(uint32_t))
               .withOutputParameterReturning("message", expected_msg, message_len)
               .andReturnValue(message_len);
}

TEST_GROUP(CanInterfaceMockTestGroup)
{
    uint32_t id;
    uint8_t msg[8];

    void teardown()
    {
        mock().checkExpectations();
        mock().clear();
    }

};


TEST(CanInterfaceMockTestGroup, CanGetNodeID)
{
    can_mock_message(42, msg, 0);

    can_interface_read_message(&id, msg);

    CHECK_EQUAL(42, id);
}

TEST(CanInterfaceMockTestGroup, CanGetMessageLength)
{
    int len;
    can_mock_message(42, (uint8_t *)"hello", 5);

    len = can_interface_read_message(&id, msg);
    CHECK_EQUAL(5, len);
}


TEST(CanInterfaceMockTestGroup, CanGetMessage)
{
    int len;
    can_mock_message(42, (uint8_t *)"hello", 5);

    can_interface_read_message(&id, msg);
    STRCMP_EQUAL("hello", (char *)msg);
}

TEST(CanInterfaceMockTestGroup, CanOutputMessage)
{
    uint8_t msg[] = {1,2,3};
    mock("can").expectOneCall("write")
               .withIntParameter("len", 3)
               .withIntParameter("id", 0x42);
    can_interface_send_message(0x42, msg, 3);

}
