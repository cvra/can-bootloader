#ifndef PLATFORM_H
#define PLATFORM_H

#ifdef __cplusplus
extern "C" {
#endif

#include <stdint.h>
#include <stddef.h>

// example sizes
#define PLATFORM_DEVICE_CLASS "test-device"
#define FLASH_PAGE_SIZE 256
#define CONFIG_PAGE_SIZE FLASH_PAGE_SIZE

extern uint8_t config_page_buffer[CONFIG_PAGE_SIZE];

void* memory_get_app_addr(void);
void* memory_get_config1_addr(void);
void* memory_get_config2_addr(void);
size_t memory_get_app_size(void);

#ifdef __cplusplus
}
#endif

#endif /* PLATFORM_H */
