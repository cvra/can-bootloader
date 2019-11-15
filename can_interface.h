#ifndef CAN_INTERFACE_H
#define CAN_INTERFACE_H

#ifdef __cplusplus
extern "C" {
#endif

#include <stdint.h>
#include <stdbool.h>

/** Reads a message from the CAN interface.
 * @param [out] id A pointer to the variable where the message ID will be stored.
 * @param [out] message A buffer where the CAN message will be stored. Should be large enough to contain 8 bytes.
 * @param [out] length A pointer to the message length.
 * @param [in] retries The number of retries until timeout.
 * @returns true if read was successful.
 */
bool can_interface_read_message(uint32_t* id, uint8_t* message, uint8_t* length, uint32_t retries);

/** Sends a message via the CAN interface.
 * @param [in] id The CAN ID to address.
 * @param [in] message The message data.
 * @param [in] length The message length.
 * @param [in] retries The number of retries until timeout.
 * @returns true if write was successful.
 */
bool can_interface_send_message(uint32_t id, uint8_t* message, uint8_t length, uint32_t retries);

#ifdef __cplusplus
}
#endif

#endif
