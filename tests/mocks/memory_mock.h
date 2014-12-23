#ifndef MEMORY_MOCK_H
#define MEMORY_MOCK_H

#ifdef __cplusplus
extern "C" {
#endif

#include "../../memory.h"

extern uint8_t config1[64];
extern uint8_t config2[64];
extern uint8_t page_buffer[64];

extern int app;

#ifdef __cplusplus
}
#endif

#endif /* MEMORY_MOCK_H */