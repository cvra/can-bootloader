#ifndef MEMORY_H
#define MEMORY_H

#ifdef __cplusplus
extern "C" {
#endif

#include <stdint.h>
#include <stddef.h>

extern const size_t config_page_size;
extern uint8_t config_page_buffer[];

void *memory_get_app_addr(void);
void *memory_get_config1_addr(void);
void *memory_get_config2_addr(void);

#ifdef __cplusplus
}
#endif

#endif /* MEMORY_H */