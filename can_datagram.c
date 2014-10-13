#include <stdlib.h>
#include <string.h>
#include "can_datagram.h"
#include <serializer/crc.h>

void can_datagram_read_crc_state(state_machine_t *machine);

void can_datagram_init(can_datagram_t *dt)
{
    memset(dt, 0, sizeof *dt);
}

void can_datagram_set_adress_buffer(can_datagram_t *dt, uint8_t *buf)
{
    dt->destination_nodes = buf;
}

void can_datagram_set_data_buffer(can_datagram_t *dt, uint8_t *buf)
{
    dt->data = buf;
}

void can_datagram_input_byte(can_datagram_t *dt, uint8_t val)
{
    switch (dt->_reader_state) {
        case 0: /* CRC */
            dt->crc = (dt->crc << 8) | val;
            dt->_crc_bytes_read ++;

            if (dt->_crc_bytes_read == 4) {
                dt->_reader_state ++;
            }
            break;

        case 1: /* Destination nodes list length */
            dt->destination_nodes_len = val;
            dt->_reader_state++;
            break;

        case 2: /* Destination nodes */
            dt->destination_nodes[dt->_destination_nodes_read] = val;
            dt->_destination_nodes_read ++;

            if (dt->_destination_nodes_read == dt->destination_nodes_len) {
                dt->_reader_state ++;
            }
            break;

        case 3: /* Data length, MSB */
            dt->data_len = val << 8;
            dt->_reader_state ++;
            break;

        case 4: /* Data length, LSB */
            dt->data_len |= val;
            dt->_reader_state ++;
            break;

        case 5: /* Data */
            dt->data[dt->_data_bytes_read] = val;
            dt->_data_bytes_read ++;

            /* Don't change state, stay here forever. */
            break;
    }
}

bool can_datagram_is_complete(can_datagram_t *dt)
{
    return dt->_reader_state > 0 && dt->_data_bytes_read == dt->data_len;
}

bool can_datagram_is_valid(can_datagram_t *dt)
{
    uint32_t crc;
    uint8_t tmp[2];
    crc = crc32(0, &dt->destination_nodes_len, 1);
    crc = crc32(crc, &dt->destination_nodes[0], 1);

    /* data_len is not in network endianess, correct that before CRC update. */
    tmp[0] = dt->data_len >> 8;
    tmp[1] = dt->data_len & 0xff;

    crc = crc32(crc, tmp, 2);
    crc = crc32(crc, &dt->data[0], dt->data_len);

    return crc == dt->crc;
}
