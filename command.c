#include "command.h"

int protocol_execute_command(char *data, command_t *commands, int command_len)
{
    serializer_t serializer;
    cmp_ctx_t command_reader;
    int commmand_index, i;
    int argc;
    bool read_success;

    // XXX size 0 should be replaced with correct size
    serializer_init(&serializer, data, 0);
    serializer_cmp_ctx_factory(&command_reader, &serializer);

    read_success = cmp_read_int(&command_reader, &commmand_index);

    if (!read_success) {
        return -ERR_INVALID_COMMAND;
    }

    read_success = cmp_read_array(&command_reader, &argc);

    /* If we cannot read array size, assume it is because we don't have
     * arguments. */
    if (!read_success) {
        argc = 0;
    }

    for (i = 0; i < command_len; ++i) {
        if (commands[i].index == commmand_index) {
            commands[i].callback(argc, &command_reader);
            return 0;
        }
    }

    return -ERR_COMMAND_NOT_FOUND;
}
