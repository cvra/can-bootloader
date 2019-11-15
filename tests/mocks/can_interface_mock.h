#ifndef CAN_INTERFACE_MOCK_H
#define CAN_INTERFACE_MOCK_H

#include <stdint.h>
#include <stdbool.h>

void can_mock_message(uint32_t message_id, uint8_t* msg, uint8_t message_len);

#endif
