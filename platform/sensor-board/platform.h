#ifndef PLATFORM_H
#define PLATFORM_H

#ifdef __cplusplus
extern "C" {
#endif

#include <stdint.h>
#include <stddef.h>

#define PLATFORM_DEVICE_CLASS "sensor-board"
#define FLASH_PAGE_SIZE 2048
#define CONFIG_PAGE_SIZE FLASH_PAGE_SIZE

extern uint8_t config_page_buffer[CONFIG_PAGE_SIZE];

// symbols defined in linkerscript
extern int application_address, application_size, config_page1, config_page2;

static inline void* memory_get_app_addr(void)
{
    return (void*)&application_address;
}

static inline size_t memory_get_app_size(void)
{
    return (size_t)&application_size;
}

static inline void* memory_get_config1_addr(void)
{
    return (void*)&config_page1;
}

static inline void* memory_get_config2_addr(void)
{
    return (void*)&config_page2;
}

#ifdef __cplusplus
}
#endif

#endif /* PLATFORM_H */
