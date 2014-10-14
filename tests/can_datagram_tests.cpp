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

    void input_data(uint8_t *data, size_t len)
    {
        for (int i = 0; i < len; ++i) {
            can_datagram_input_byte(&datagram, data[i]);
        }
    }
};

TEST(CANDatagramInputTestGroup, CANReadCRC)
{
    uint8_t buf[] = {0xde, 0xad, 0xbe, 0xef};
    input_data(buf, sizeof buf);

    CHECK_EQUAL(0xdeadbeef, datagram.crc);
}

TEST(CANDatagramInputTestGroup, CanReadDestinationLength)
{
    uint8_t buf[] = {0x00, 0x00, 0x00, 0x00, 42};

    input_data(buf, sizeof buf);

    CHECK_EQUAL(42, datagram.destination_nodes_len);
}

TEST(CANDatagramInputTestGroup, CanReadDestinations)
{
    int i;

    uint8_t buf[] = {
        0x00, 0x00, 0x00, 0x00, // CRC
        5, // destination node list length
        2, 3 // destination nodes
    };

    input_data(buf, sizeof buf);

    CHECK_EQUAL(2, datagram.destination_nodes[0]);
    CHECK_EQUAL(3, datagram.destination_nodes[1]);
}

TEST(CANDatagramInputTestGroup, CanReadDataLength)
{
    // Data length
    const int len = 12;

    uint8_t buf[] = {
        0x00, 0x00, 0x00, 0x00, // CRC
        1, // destination node list length
        3, // destination nodes
        len >> 8,  // data length (MSB)
        len & 0xff // data length (LSB)
    };

    input_data(buf, sizeof buf);

    CHECK_EQUAL(len, datagram.data_len);
}

TEST(CANDatagramInputTestGroup, CanReadData)
{
    // Data
    char *data = (char *)"Hello";
    int len = strlen(data);

    uint8_t buf[] = {
        0x00, 0x00, 0x00, 0x00, // CRC
        1, // destination node list length
        3, // destination nodes
        len >> 8,  // data length (MSB)
        len & 0xff // data length (LSB)
    };

    input_data(buf, sizeof buf);

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
    int len = 1;
    uint8_t buf[] = {
        0x00, 0x00, 0x00, 0x00, // CRC
        1, // destination node list length
        3, // destination nodes
        len >> 8,  // data length (MSB)
        len & 0xff,// data length (LSB)
        0x42 // data
    };

    input_data(buf, sizeof buf);

    CHECK_TRUE(can_datagram_is_complete(&datagram));
}

TEST(CANDatagramInputTestGroup, IsInvalidOnCRCMismatch)
{
    int len = 1;
    uint8_t buf[] = {
        0x00, 0x00, 0x00, 0x00, // CRC
        1, // destination node list length
        3, // destination nodes
        len >> 8,  // data length (MSB)
        len & 0xff,// data length (LSB)
        0x42 // data
    };

    input_data(buf, sizeof buf);

    CHECK_FALSE(can_datagram_is_valid(&datagram));
}

TEST(CANDatagramInputTestGroup, IsValidWhenAllDataAreReadAndCRCMatches)
{
    int len = 1;
    uint8_t buf[] = {
        0x9a, 0x54, 0xb8, 0x63, // CRC
        1, // destination node list length
        14, // destination nodes
        len >> 8,  // data length (MSB)
        len & 0xff,// data length (LSB)
        0x42 // data
    };

    input_data(buf, sizeof buf);

    CHECK_TRUE(can_datagram_is_valid(&datagram));
}

TEST(CANDatagramInputTestGroup, DoesNotAppendMoreBytesThanDataLen)
{
    /** This test checks that if bytes arrive after the specified data length, they
     * are simply discarded. */
    int len = 1;
    uint8_t buf[] = {
        0x9a, 0x54, 0xb8, 0x63, // CRC
        1, // destination node list length
        14, // destination nodes
        len >> 8,  // data length (MSB)
        len & 0xff,// data length (LSB)
        0x42, // data
        0x43, 0x44 // garbage value
    };

    input_data(buf, sizeof buf);

    CHECK_EQUAL(0x42, datagram.data[0]);
    CHECK_EQUAL(0, datagram.data[1]);
}

TEST(CANDatagramInputTestGroup, DoesNotOverflowDataBuffer)
{
    /** This test checks that if bytes arrive after the specified data length, they
     * are simply discarded. */

    // Pass a smaller size (5) to check overflow detection
    can_datagram_set_data_buffer(&datagram, data_buffer, 5);

    char data[] = "hello, world"; // too long to fit in buffer !
    int len = strlen(data);

    uint8_t buf[] = {
        0x9a, 0x54, 0xb8, 0x63, // CRC
        1, // destination node list length
        14, // destination nodes
        len >> 8,  // data length (MSB)
        len & 0xff,// data length (LSB)
    };

    input_data(buf, sizeof buf);

    for (int i = 0; i < len; ++i) {
        can_datagram_input_byte(&datagram, data[i]);
    }

    /* Check that we respected the limit. */
    STRCMP_EQUAL("hello", (char *)datagram.data);
}

TEST(CANDatagramInputTestGroup, CanResetToStart)
{
    // Writes some part of a datagram, like after a hotplug
    for (int i = 0; i < 20; ++i) {
        can_datagram_input_byte(&datagram, 3);
    }


    // We see the start of a datagram and start inputing the beginning of a
    // valid packet.
    can_datagram_start(&datagram);

    int len = 1;
    uint8_t buf[] = {
        0xde, 0xad, 0xbe, 0xef,  // CRC
        1, // destination node list length
        14, // destination nodes
        len >> 8,  // data length (MSB)
        len & 0xff,// data length (LSB)
        42 // data
    };

    input_data(buf, sizeof buf);

    CHECK_EQUAL(0xdeadbeef, datagram.crc);
    CHECK_EQUAL(1, datagram.destination_nodes_len);
    CHECK_EQUAL(14, datagram.destination_nodes[0]);
    CHECK_EQUAL(1, datagram.data_len);
    CHECK_EQUAL(42, datagram.data[0]);
}
