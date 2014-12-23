#include "memory_mock.h"

uint8_t config1[64];
uint8_t config2[64];
uint8_t page_buffer[64];
const size_t page_size = sizeof(page_buffer);

int app;

void *memory_get_app_addr(void)
{
    return &app;
}

void *memory_get_config1_addr(void)
{
    return &config1[0];
}

void *memory_get_config2_addr(void)
{
    return &config2[0];
}

