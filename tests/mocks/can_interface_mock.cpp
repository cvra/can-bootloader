#include "../../can_interface.h"
#include "CppUTest/TestHarness.h"
#include "CppUTestExt/MockSupport.h"

#include <cstring>

static uint32_t expected_id;
static uint8_t expected_len;
uint8_t expected_msg[8];

bool can_interface_read_message(uint32_t* id, uint8_t* message, uint8_t* length, uint32_t retries)
{
    mock("can").actualCall("read").withOutputParameter("id", id).withOutputParameter("message", message).withOutputParameter("length", length);
    return true;
}

bool can_interface_send_message(uint32_t id, uint8_t* message, uint8_t length, uint32_t retries)
{
    mock("can").actualCall("send").withParameter("id", id).withParameter("message", message).withParameter("length", length);
    return true;
}

void can_mock_message(uint32_t message_id, uint8_t* msg, uint8_t message_len)
{
    expected_id = message_id;
    expected_len = message_len;
    memcpy(expected_msg, msg, message_len);

    mock("can").expectOneCall("read").withOutputParameterReturning("id", &expected_id, sizeof(uint32_t)).withOutputParameterReturning("message", expected_msg, message_len).withOutputParameterReturning("length", &expected_len, sizeof(uint8_t));
}

TEST_GROUP (CanInterfaceMockTestGroup) {
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
    uint8_t len;

    can_mock_message(42, msg, 0);

    can_interface_read_message(&id, msg, &len, 1);

    CHECK_EQUAL(42, id);
}

TEST(CanInterfaceMockTestGroup, CanGetMessageLength)
{
    uint8_t len;

    can_mock_message(42, (uint8_t*)"hello", 5);

    can_interface_read_message(&id, msg, &len, 1);
    CHECK_EQUAL(5, len);
}

TEST(CanInterfaceMockTestGroup, CanGetMessage)
{
    uint8_t len;

    can_mock_message(42, (uint8_t*)"hello", 5);

    can_interface_read_message(&id, msg, &len, 1);
    STRCMP_EQUAL("hello", (char*)msg);
}

TEST(CanInterfaceMockTestGroup, CanOutputMessage)
{
    uint8_t msg[] = {1, 2, 3};
    mock("can").expectOneCall("send").withIntParameter("length", 3).withParameter("message", msg).withIntParameter("id", 0x42);
    can_interface_send_message(0x42, msg, 3, 1);
}
