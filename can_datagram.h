#ifndef CAN_DATAGRAM_H
#define CAN_DATAGRAM_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

#define CAN_DATAGRAM_VERSION 1

#define ID_START_MASK (1 << 7)

typedef struct {
    int protocol_version;
    uint32_t crc;

    uint8_t destination_nodes_len;
    uint8_t* destination_nodes;

    uint32_t data_len;
    uint8_t* data;

    int _crc_bytes_read;
    int _crc_bytes_written;
    int _data_length_bytes_read;
    int _data_length_bytes_written;
    uint8_t _destination_nodes_read;
    uint8_t _destination_nodes_written;
    uint16_t _data_bytes_read;
    uint16_t _data_bytes_written;
    uint16_t _data_buffer_size;
    int _reader_state;
    int _writer_state;
} can_datagram_t;

/** Sets the structure field to default values. */
void can_datagram_init(can_datagram_t* dt);

/** Sets the buffer to use to store destination addresses. */
void can_datagram_set_address_buffer(can_datagram_t* dt, uint8_t* buf);

/** Sets the buffer to use for data storage. */
void can_datagram_set_data_buffer(can_datagram_t* dt, uint8_t* buf, size_t buf_size);

/** Inputs a byte into the datagram. */
void can_datagram_input_byte(can_datagram_t* dt, uint8_t val);

/** Returns true if the datagram is complete (all data were read). */
bool can_datagram_is_complete(can_datagram_t* dt);

/** Returns true if the datagram is valid (complete and CRC match). */
bool can_datagram_is_valid(can_datagram_t* dt);

/** Signals to the parser that we are at the start of a datagram.
 *
 * The start of datagram comes from the Message ID (physical layer).
 */
void can_datagram_start(can_datagram_t* dt);

/** Encodes the datagram in the buffer. */
int can_datagram_output_bytes(can_datagram_t* dt, char* buffer, size_t buffer_len);

/** Computes the CRC32 of the datagram. */
uint32_t can_datagram_compute_crc(can_datagram_t* dt);

/** Returns true if the ID has the start of datagram field set. */
bool can_datagram_id_start_is_set(unsigned int id);

#ifdef __cplusplus
}
#endif

#endif
