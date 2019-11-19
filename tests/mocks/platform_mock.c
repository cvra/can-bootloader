#include <platform.h>

uint8_t memory_mock_config1[CONFIG_PAGE_SIZE];
uint8_t memory_mock_config2[CONFIG_PAGE_SIZE];
uint8_t memory_mock_app[42];

uint8_t config_page_buffer[CONFIG_PAGE_SIZE];

void* memory_get_app_addr(void)
{
    return &memory_mock_app[0];
}

void* memory_get_config1_addr(void)
{
    return &memory_mock_config1[0];
}

void* memory_get_config2_addr(void)
{
    return &memory_mock_config2[0];
}

size_t memory_get_app_size(void)
{
    return sizeof(memory_mock_app);
}
