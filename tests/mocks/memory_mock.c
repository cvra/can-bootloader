#include "memory_mock.h"

uint8_t memory_mock_config1[64];
uint8_t memory_mock_config2[64];
uint8_t memory_mock_app[42];

uint8_t page_buffer[64];
const size_t page_size = sizeof(page_buffer);

void *memory_get_app_addr(void)
{
    return &memory_mock_app[0];
}

void *memory_get_config1_addr(void)
{
    return &memory_mock_config1[0];
}

void *memory_get_config2_addr(void)
{
    return &memory_mock_config2[0];
}

