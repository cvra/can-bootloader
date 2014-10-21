#ifndef COMMAND_H_
#define COMMAND_H_

#include <serializer/serialization.h>

#ifdef __cplusplus
extern "C" {
#endif

/** Invalid command format.
 *
 * Means that the command format is invalid, for example if the command index
 * is not an integer. */
#define ERR_INVALID_COMMAND 1

/** Command index could not be found in command table. */
#define ERR_COMMAND_NOT_FOUND 2

typedef struct {
    /** Command ID */
    uint8_t index;
    /** The callback function for this entry.
     *
     * @param [in] argc Argument count
     * @param [in] arg_context MessagePack context containing the parameters.
     * @param [in] out_context MessagePack context in which the output data should be written.
     */
    void (*callback)(int, cmp_ctx_t *, cmp_ctx_t *);
} command_t;

/** Parses a datagram data field and executes the correct function.
 * @param [in] data The raw data to parse.
 * @param [in] commands A list of all possible commands.
 * @param [in] command_len Length of the commands array.
 * @param [out] output_buffer A buffer where the command can place its results, which will be sent back to the client.
 */
int protocol_execute_command(char *data, command_t *commands, int command_len, char *output_buffer);

#ifdef __cplusplus
}
#endif


#endif
