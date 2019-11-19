#include "CppUTest/TestHarness.h"
#include "CppUTestExt/MockSupport.h"

#include <cstring>

#include "../can_datagram.h"

TEST_GROUP (CANDatagramTestGroup) {
    can_datagram_t dt;
    uint8_t address_buffer[128];
    uint8_t data_buffer[128];

    void setup(void)
    {
        can_datagram_init(&dt);
        can_datagram_set_address_buffer(&dt, address_buffer);
        can_datagram_set_data_buffer(&dt, data_buffer, sizeof data_buffer);
    }
};

TEST(CANDatagramTestGroup, CanInitDatagram)
{
    /* fill the struct with garbage. */
    memset(&dt, 0xaa, sizeof dt);

    /* Inits the datagram */
    can_datagram_init(&dt);

    CHECK_EQUAL(0, dt.crc);
    CHECK_EQUAL(0, dt.destination_nodes_len);
    CHECK_EQUAL(0, dt.data_len);
}

TEST(CANDatagramTestGroup, CanSetDestinationAdressesBuffer)
{
    uint8_t buf[10];
    can_datagram_set_address_buffer(&dt, buf);

    POINTERS_EQUAL(buf, dt.destination_nodes);
}

TEST(CANDatagramTestGroup, CanSetDataBuffer)
{
    uint8_t buf[10];
    can_datagram_set_data_buffer(&dt, buf, sizeof buf);
    POINTERS_EQUAL(buf, dt.data);
}

TEST(CANDatagramTestGroup, CanComputeCRC)
{
    dt.destination_nodes_len = 1;
    dt.destination_nodes[0] = 14;
    dt.data_len = 1;
    dt.data[0] = 0x42;

    CHECK_EQUAL(0x80d8a447, can_datagram_compute_crc(&dt));
}

TEST_GROUP (CANDatagramInputTestGroup) {
    can_datagram_t datagram;
    uint8_t address_buffer[128];
    uint8_t data_buffer[128];

    void setup(void)
    {
        can_datagram_init(&datagram);
        can_datagram_set_address_buffer(&datagram, address_buffer);
        can_datagram_set_data_buffer(&datagram, data_buffer, sizeof data_buffer);
    }

    void input_data(uint8_t * data, size_t len)
    {
        for (int i = 0; i < len; ++i) {
            can_datagram_input_byte(&datagram, data[i]);
        }
    }
};

TEST(CANDatagramInputTestGroup, ReadProtocolVersion)
{
    uint8_t buf[] = {1};
    input_data(buf, sizeof buf);
    CHECK_EQUAL(1, datagram.protocol_version);
}

TEST(CANDatagramInputTestGroup, CANReadCRC)
{
    uint8_t buf[] = {0x01, 0xde, 0xad, 0xbe, 0xef};
    input_data(buf, sizeof buf);

    CHECK_EQUAL(0xdeadbeef, datagram.crc);
}

TEST(CANDatagramInputTestGroup, CanReadDestinationLength)
{
    uint8_t buf[] = {0x01, 0x00, 0x00, 0x00, 0x00, 42};

    input_data(buf, sizeof buf);

    CHECK_EQUAL(42, datagram.destination_nodes_len);
}

TEST(CANDatagramInputTestGroup, CanReadDestinations)
{
    uint8_t buf[] = {
        0x01, // protocol version
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
    uint8_t buf[] = {
        0x01, // protocol version
        0x00, 0x00, 0x00, 0x00, // CRC
        1, // destination node list length
        3, // destination nodes
        0xca, 0xfe, 0xba, 0xbe // data length
    };

    input_data(buf, sizeof buf);

    CHECK_EQUAL(0xcafebabe, datagram.data_len);
}

TEST(CANDatagramInputTestGroup, CanReadData)
{
    // Data
    char* data = (char*)"Hello";
    int len = strlen(data);

    uint8_t buf[] = {
        0x01, // protocol version
        0x00, 0x00, 0x00, 0x00, // CRC
        1, // destination node list length
        3, // destination nodes
        0x00, 0x00, 0x00, (uint8_t)(len & 0xff) // data length
    };

    input_data(buf, sizeof buf);

    for (int i = 0; i < len; ++i) {
        can_datagram_input_byte(&datagram, data[i]);
    }

    STRCMP_EQUAL(data, (char*)datagram.data);
}

TEST(CANDatagramInputTestGroup, EmptyDatagramIsNotComplete)
{
    CHECK_FALSE(can_datagram_is_complete(&datagram));
}

TEST(CANDatagramInputTestGroup, IsCompleteWhenAllDataAreRead)
{
    uint8_t buf[] = {
        0x01, // protocol version
        0x00, 0x00, 0x00, 0x00, // CRC
        1, // destination node list length
        3, // destination nodes
        0x00, 0x00, 0x00, 0x01, // data length
        0x42 // data
    };

    input_data(buf, sizeof buf);

    CHECK_TRUE(can_datagram_is_complete(&datagram));
}

TEST(CANDatagramInputTestGroup, IsNotCompleteWhenReadInProgress)
{
    uint8_t buf[] = {
        0x01, // protocol version
        0x00, 0x00, 0x00, 0x00, // CRC
        1, // destination node list length
        3, // destination nodes
        0x00, 0x00, 0x00, 0x01, // data length
        0x42};

    input_data(&buf[0], 8);

    CHECK_FALSE(can_datagram_is_complete(&datagram));

    input_data(&buf[8], sizeof(buf) - 8);

    CHECK_TRUE(can_datagram_is_complete(&datagram));
}

TEST(CANDatagramInputTestGroup, IsInvalidOnCRCMismatch)
{
    int len = 1;
    uint8_t buf[] = {
        0x01, // protocol version
        0x00, 0x00, 0x00, 0x00, // CRC
        1, // destination node list length
        3, // destination nodes
        (uint8_t)(len >> 8), // data length (MSB)
        (uint8_t)(len & 0xff), // data length (LSB)
        0x42 // data
    };

    input_data(buf, sizeof buf);

    CHECK_FALSE(can_datagram_is_valid(&datagram));
}

TEST(CANDatagramInputTestGroup, IsValidWhenAllDataAreReadAndCRCMatches)
{
    uint8_t buf[] = {
        0x01, // protocol version
        0x80, 0xd8, 0xa4, 0x47, // CRC
        1, // destination node list length
        14, // destination nodes
        0x00, 0x00, 0x00, 0x01, // data length
        0x42 // data
    };

    input_data(buf, sizeof buf);

    CHECK_TRUE(can_datagram_is_valid(&datagram));
}

TEST(CANDatagramInputTestGroup, IsInvalidIfProtocolVersionDoesntMatch)
{
    uint8_t buf[] = {
        0x40, // wrong protocol version
        0x80, 0xd8, 0xa4, 0x47, // CRC
        1, // destination node list length
        14, // destination nodes
        0x00, 0x00, 0x00, 0x01, // data length
        0x42 // data
    };

    input_data(buf, sizeof buf);
    CHECK_FALSE(can_datagram_is_valid(&datagram));
}

TEST(CANDatagramInputTestGroup, CRCIsComputedInMoreThanOneDestinationNodeAndData)
{
    uint8_t buf[] = {
        0x01, // protocol version
        0x05, 0x23, 0xb7, 0x30,
        2, // destination node list length
        14, 15, // destination nodes
        0x00, 0x00, 0x00, 0x02, // data length
        0x42, 0x43 // data
    };

    input_data(buf, sizeof buf);

    CHECK_TRUE(can_datagram_is_valid(&datagram));
}

TEST(CANDatagramInputTestGroup, DoesNotAppendMoreBytesThanDataLen)
{
    /** This test checks that if bytes arrive after the specified data length, they
     * are simply discarded. */
    uint8_t buf[] = {
        0x01, // protocol version
        0x9a, 0x54, 0xb8, 0x63, // CRC
        1, // destination node list length
        14, // destination nodes
        0x00, 0x00, 0x00, 0x01, // data length
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
    uint8_t len = strlen(data);

    uint8_t buf[] = {
        0x01, // protocol version
        0x9a, 0x54, 0xb8, 0x63, // CRC
        1, // destination node list length
        14, // destination nodes
        0x00, 0x00, 0x00, len // data length
    };

    input_data(buf, sizeof buf);

    for (int i = 0; i < len; ++i) {
        can_datagram_input_byte(&datagram, data[i]);
    }

    /* Check that we respected the limit. */
    STRCMP_EQUAL("hello", (char*)datagram.data);
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

    uint8_t buf[] = {
        0x01, // protocol version
        0xde, 0xad, 0xbe, 0xef, // CRC
        1, // destination node list length
        14, // destination nodes
        0x00, 0x00, 0x00, 0x01, // data length
        42 // data
    };

    input_data(buf, sizeof buf);

    CHECK_EQUAL(0xdeadbeef, datagram.crc);
    CHECK_EQUAL(1, datagram.destination_nodes_len);
    CHECK_EQUAL(14, datagram.destination_nodes[0]);
    CHECK_EQUAL(1, datagram.data_len);
    CHECK_EQUAL(42, datagram.data[0]);
}

TEST_GROUP (CANDatagramOutputTestGroup) {
    can_datagram_t datagram;
    uint8_t address_buffer[128];
    uint8_t data_buffer[128];

    char output[64];
    int ret;

    void setup(void)
    {
        can_datagram_init(&datagram);
        can_datagram_set_address_buffer(&datagram, address_buffer);
        can_datagram_set_data_buffer(&datagram, data_buffer, sizeof data_buffer);
        memset(output, 0, sizeof output);
    }
};

TEST(CANDatagramOutputTestGroup, CanOutputProtocolVersion)
{
    ret = can_datagram_output_bytes(&datagram, output, 1);
    CHECK_EQUAL(1, ret);
    BYTES_EQUAL(0x01, output[0]);
}

TEST(CANDatagramOutputTestGroup, CanOutputCRC)
{
    datagram.crc = 0xdeadbeef;

    ret = can_datagram_output_bytes(&datagram, output, 5);

    BYTES_EQUAL(0xde, output[1]);
    BYTES_EQUAL(0xad, output[2]);
    BYTES_EQUAL(0xbe, output[3]);
    BYTES_EQUAL(0xef, output[4]);
    CHECK_EQUAL(5, ret);
}

TEST(CANDatagramOutputTestGroup, CanStopMidCRC)
{
    datagram.crc = 0xdeadbeef;

    // Only output 2 bytes
    ret = can_datagram_output_bytes(&datagram, output, 3);

    CHECK_EQUAL(3, ret);
    BYTES_EQUAL(0xde, output[1]);
    BYTES_EQUAL(0xad, output[2]);
    BYTES_EQUAL(0x00, output[3]);
}

TEST(CANDatagramOutputTestGroup, CanStopMidCRCAndRestart)
{
    datagram.crc = 0xdeadbeef;

    // Only output 2 bytes
    can_datagram_output_bytes(&datagram, output, 3);

    // Writes the next two bytes
    ret = can_datagram_output_bytes(&datagram, output, 2);

    CHECK_EQUAL(2, ret);
    BYTES_EQUAL(0xbe, output[0]);
    BYTES_EQUAL(0xef, output[1]);
}

TEST(CANDatagramOutputTestGroup, CanOutputDestinationNodeList)
{
    datagram.destination_nodes_len = 2;
    datagram.destination_nodes[0] = 42;
    datagram.destination_nodes[1] = 43;

    can_datagram_output_bytes(&datagram, output, 8);

    BYTES_EQUAL(2, output[5]);
    BYTES_EQUAL(42, output[6]);
    BYTES_EQUAL(43, output[7]);
}

TEST(CANDatagramOutputTestGroup, CanOutputDataLength)
{
    datagram.destination_nodes_len = 1;
    datagram.destination_nodes[0] = 12;

    datagram.data_len = 0xcafebabe;

    can_datagram_output_bytes(&datagram, output, 11);

    BYTES_EQUAL(0xca, output[7]);
    BYTES_EQUAL(0xfe, output[8]);
    BYTES_EQUAL(0xba, output[9]);
    BYTES_EQUAL(0xbe, output[10]);
}

TEST(CANDatagramOutputTestGroup, CanOutputData)
{
    datagram.destination_nodes_len = 1;
    datagram.destination_nodes[0] = 12;

    datagram.data_len = 2;
    datagram.data[0] = 42;
    datagram.data[1] = 43;

    can_datagram_output_bytes(&datagram, output, 13);

    BYTES_EQUAL(42, output[11]);
    BYTES_EQUAL(43, output[12]);
}

TEST(CANDatagramOutputTestGroup, IfWeStopEarlierBytesWrittenIsReturned)
{
    int ret;
    datagram.destination_nodes_len = 1;
    datagram.destination_nodes[0] = 12;

    datagram.data_len = 2;
    datagram.data[0] = 42;
    datagram.data[1] = 43;

    // Output the first 10 bytes
    can_datagram_output_bytes(&datagram, output, 10);

    // So now we only have three bytes to send, but we ask for more
    ret = can_datagram_output_bytes(&datagram, output, 10);

    CHECK_EQUAL(3, ret);
}

TEST_GROUP (CANIDTestGroup) {
};

TEST(CANIDTestGroup, CanFindIfStartOfDatagram)
{
    int source_id = 0x2;
    int start_bit = (1 << 7);
    CHECK_FALSE(can_datagram_id_start_is_set(source_id));
    CHECK_TRUE(can_datagram_id_start_is_set(source_id | start_bit));
}
