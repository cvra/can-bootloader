#include "command.h"

void protocol_execute_command(char *data, command_t *commands, int command_len)
{
    serializer_t serializer;
    cmp_ctx_t command_reader;
    int commmand_index, i;
    int argc;

    // XXX size 0 should be replaced with correct size
    serializer_init(&serializer, data, 0);
    serializer_cmp_ctx_factory(&command_reader, &serializer);

    // TODO correct error handling
    cmp_read_int(&command_reader, &commmand_index);
    cmp_read_array(&command_reader, &argc);

    for (i = 0; i < command_len; ++i) {
        if (commands[i].index == commmand_index) {
            commands[i].f(argc, &command_reader);
            break;
        }
    }
}
