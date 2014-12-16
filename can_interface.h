#ifndef CAN_INTERFACE_H
#define CAN_INTERFACE_H

#ifdef __cplusplus
extern "C" {
#endif

#include <stdint.h>

/** Reads a message from the CAN interface.
 *
 * @param [out] message_id A pointer to the variable where the message ID will be stored.
 * @param [out] message A buffer where the CAN message will be stored. Should be large enough to contain 8 bytes.
 * @returns The number of bytes in the message.
 */
int can_interface_read_message(uint32_t *message_id, uint8_t *message);

void can_interface_send_message(uint32_t message_id, uint8_t *message, int len);

#ifdef __cplusplus
}
#endif


#endif
