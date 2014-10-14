#include "CppUTest/TestHarness.h"
#include "CppUTestExt/MockSupport.h"

#include <cstring>

#include "../can_datagram.h"

TEST_GROUP(CanDataGramTestGroup)
{
    can_datagram_t dt;

    void setup(void)
    {
        can_datagram_init(&dt);
    }
};

TEST(CanDataGramTestGroup, CanInitDatagram)
{
    /* fill the struct with garbage. */
    memset(&dt, 0xaa, sizeof dt);

    /* Inits the datagram */
    can_datagram_init(&dt);

    CHECK_EQUAL(0, dt.crc);
    CHECK_EQUAL(0, dt.destination_nodes_len);
    CHECK_EQUAL(0, dt.data_len);
}

TEST(CanDataGramTestGroup, CanSetDestinationAdressesBuffer)
{
    uint8_t buf[10];
    can_datagram_set_adress_buffer(&dt, buf);

    POINTERS_EQUAL(buf, dt.destination_nodes);
}

TEST(CanDataGramTestGroup, CanSetDataBuffer)
{
    uint8_t buf[10];
    can_datagram_set_data_buffer(&dt, buf, sizeof buf);
    POINTERS_EQUAL(buf, dt.data);
}

TEST_GROUP(CANDatagramInputTestGroup)
{
    can_datagram_t datagram;
    uint8_t adress_buffer[128];
    uint8_t data_buffer[128];

    void setup(void)
    {
        can_datagram_init(&datagram);
        can_datagram_set_adress_buffer(&datagram, adress_buffer);
        can_datagram_set_data_buffer(&datagram, data_buffer, sizeof data_buffer);
    }
};

TEST(CANDatagramInputTestGroup, CANReadCRC)
{
    can_datagram_input_byte(&datagram, 0xde);
    can_datagram_input_byte(&datagram, 0xad);
    can_datagram_input_byte(&datagram, 0xbe);
    can_datagram_input_byte(&datagram, 0xef);

    CHECK_EQUAL(0xdeadbeef, datagram.crc);
}

TEST(CANDatagramInputTestGroup, CanReadDestinationLength)
{
    // Input dummy CRC
    for (int i = 0; i < 4; ++i) {
        can_datagram_input_byte(&datagram, 0x00);
    }

    // Input destination list length
    can_datagram_input_byte(&datagram, 42);

    CHECK_EQUAL(42, datagram.destination_nodes_len);
}

TEST(CANDatagramInputTestGroup, CanReadDestinations)
{
    int i;
    // Input dummy CRC
    for (i = 0; i < 4; ++i) {
        can_datagram_input_byte(&datagram, 0x00);
    }

    // Input destination list length
    can_datagram_input_byte(&datagram, 5);

    // Input destinations
    for (i = 0; i < 5; ++i) {
        can_datagram_input_byte(&datagram, 10 + i);
    }

    for (i = 0; i < 5; ++i) {
        CHECK_EQUAL(10 + i, datagram.destination_nodes[i]);
    }
}

TEST(CANDatagramInputTestGroup, CanReadDataLength)
{
    // CRC
    can_datagram_input_byte(&datagram, 0x00);
    can_datagram_input_byte(&datagram, 0x00);
    can_datagram_input_byte(&datagram, 0x00);
    can_datagram_input_byte(&datagram, 0x00);

    // destination list length
    can_datagram_input_byte(&datagram, 1);

    // Destination node
    can_datagram_input_byte(&datagram, 14);

    // Data length
    const int len = 12;
    can_datagram_input_byte(&datagram, len >> 8);
    can_datagram_input_byte(&datagram, len & 0xff);

    CHECK_EQUAL(12, datagram.data_len);
}

TEST(CANDatagramInputTestGroup, CanReadData)
{
    // CRC
    can_datagram_input_byte(&datagram, 0x00);
    can_datagram_input_byte(&datagram, 0x00);
    can_datagram_input_byte(&datagram, 0x00);
    can_datagram_input_byte(&datagram, 0x00);

    // destination list length
    can_datagram_input_byte(&datagram, 1);

    // Destination node
    can_datagram_input_byte(&datagram, 14);

    // Data
    char *data = (char *)"Hello";
    int len = strlen(data);

    can_datagram_input_byte(&datagram, len >> 8);
    can_datagram_input_byte(&datagram, len & 0xff);

    for (int i = 0; i < len; ++i) {
        can_datagram_input_byte(&datagram, data[i]);
    }

    STRCMP_EQUAL(data, (char *)datagram.data);
}

TEST(CANDatagramInputTestGroup, EmptyDatagramIsNotComplete)
{
    CHECK_FALSE(can_datagram_is_complete(&datagram));
}

TEST(CANDatagramInputTestGroup, IsCompleteWhenAllDataAreRead)
{
    // CRC
    can_datagram_input_byte(&datagram, 0x00);
    can_datagram_input_byte(&datagram, 0x00);
    can_datagram_input_byte(&datagram, 0x00);
    can_datagram_input_byte(&datagram, 0x00);

    // destination list length
    can_datagram_input_byte(&datagram, 1);

    // Destination node
    can_datagram_input_byte(&datagram, 14);

    int len = 1;
    can_datagram_input_byte(&datagram, len >> 8);
    can_datagram_input_byte(&datagram, len & 0xff);

    can_datagram_input_byte(&datagram, 0x42);

    CHECK_TRUE(can_datagram_is_complete(&datagram));
}

TEST(CANDatagramInputTestGroup, IncompleteDatagramIsInvalid)
{
    CHECK_FALSE(can_datagram_is_valid(&datagram));
}

TEST(CANDatagramInputTestGroup, IsInvalidOnCRCMismatch)
{
    // CRC
    can_datagram_input_byte(&datagram, 0x00);
    can_datagram_input_byte(&datagram, 0x00);
    can_datagram_input_byte(&datagram, 0x00);
    can_datagram_input_byte(&datagram, 0x00);

    // destination list length
    can_datagram_input_byte(&datagram, 1);

    // Destination node
    can_datagram_input_byte(&datagram, 14);

    int len = 1;
    can_datagram_input_byte(&datagram, len >> 8);
    can_datagram_input_byte(&datagram, len & 0xff);

    can_datagram_input_byte(&datagram, 0x42);

    CHECK_FALSE(can_datagram_is_valid(&datagram));
}

TEST(CANDatagramInputTestGroup, IsValidWhenAllDataAreReadAndCRCMatches)
{
    // CRC
    can_datagram_input_byte(&datagram, 0x9a);
    can_datagram_input_byte(&datagram, 0x54);
    can_datagram_input_byte(&datagram, 0xb8);
    can_datagram_input_byte(&datagram, 0x63);

    // destination list length
    can_datagram_input_byte(&datagram, 1);

    // Destination node
    can_datagram_input_byte(&datagram, 14);

    int len = 1;
    can_datagram_input_byte(&datagram, len >> 8);
    can_datagram_input_byte(&datagram, len & 0xff);

    can_datagram_input_byte(&datagram, 0x42);

    CHECK_TRUE(can_datagram_is_valid(&datagram));
}

TEST(CANDatagramInputTestGroup, DoesNotAppendMoreBytesThanDataLen)
{
    /** This test checks that if bytes arrive after the specified data length, they
     * are simply discarded. */

    // CRC
    can_datagram_input_byte(&datagram, 0x00);
    can_datagram_input_byte(&datagram, 0x00);
    can_datagram_input_byte(&datagram, 0x00);
    can_datagram_input_byte(&datagram, 0x00);

    // destination list length
    can_datagram_input_byte(&datagram, 1);

    // Destination node
    can_datagram_input_byte(&datagram, 14);

    int len = 1;
    can_datagram_input_byte(&datagram, len >> 8);
    can_datagram_input_byte(&datagram, len & 0xff);

    can_datagram_input_byte(&datagram, 42);
    can_datagram_input_byte(&datagram, 43);

    CHECK_EQUAL(42, datagram.data[0]);
    CHECK_EQUAL(0, datagram.data[1]);
}

TEST(CANDatagramInputTestGroup, DoesNotOverflowDataBuffer)
{
    // Pass a smaller size (5) to check overflow detection
    can_datagram_set_data_buffer(&datagram, data_buffer, 5);

    // CRC
    can_datagram_input_byte(&datagram, 0x00);
    can_datagram_input_byte(&datagram, 0x00);
    can_datagram_input_byte(&datagram, 0x00);
    can_datagram_input_byte(&datagram, 0x00);

    // destination list length
    can_datagram_input_byte(&datagram, 1);

    // Destination node
    can_datagram_input_byte(&datagram, 14);

    char data[] = "hello, world"; // too long to fit in buffer !
    int len = strlen(data);

    can_datagram_input_byte(&datagram, len >> 8);
    can_datagram_input_byte(&datagram, len & 0xff);

    for (int i = 0; i < len; ++i) {
        can_datagram_input_byte(&datagram, data[i]);
    }

    CHECK_EQUAL(5, datagram._data_buffer_size);

    /* Check that we respected the limit. */
    STRCMP_EQUAL("hello", (char *)datagram.data);
}
