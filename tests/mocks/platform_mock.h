#ifndef PLATFORM_MOCK_H
#define PLATFORM_MOCK_H

#ifdef __cplusplus
extern "C" {
#endif

#include <platform.h>

extern uint8_t memory_mock_config1[CONFIG_PAGE_SIZE];
extern uint8_t memory_mock_config2[CONFIG_PAGE_SIZE];
extern uint8_t memory_mock_app[42];

extern uint8_t config_page_buffer[CONFIG_PAGE_SIZE];

#ifdef __cplusplus
}
#endif

#endif /* PLATFORM_MOCK_H */
