#ifndef CAN_INTERFACE_MOCK_H
#define CAN_INTERFACE_MOCK_H

// Simulates the reception of a single message
void can_mock_message(uint32_t message_id, uint8_t *msg, int message_len);


#endif
