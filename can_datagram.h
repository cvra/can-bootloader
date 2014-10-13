#ifndef CAN_DATAGRAM_H
#define CAN_DATAGRAM_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#include <state-machine/state_machine.h>

typedef struct {
    uint32_t crc;

    uint8_t *destination_nodes;
    uint8_t destination_nodes_len;

    uint8_t *data;
    uint16_t data_len;

    int _crc_bytes_read;
    uint8_t _destination_nodes_read;
    uint16_t _data_bytes_read;
    int _reader_state;
} can_datagram_t;

/** Sets the structure field to default values. */
void can_datagram_init(can_datagram_t *dt);

/** Sets the buffer to use to store destination adresses. */
void can_datagram_set_adress_buffer(can_datagram_t *dt, uint8_t *buf);

/** Sets the buffer to use for data storage. */
void can_datagram_set_data_buffer(can_datagram_t *dt, uint8_t *buf);

/** Inputs a byte into the datagram. */
void can_datagram_input_byte(can_datagram_t *dt, uint8_t val);

#ifdef __cplusplus
}
#endif

#endif
