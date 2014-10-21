#ifndef CONFIG_H
#define CONFIG_H

#ifdef __cplusplus
extern "C" {
#endif

#include <stdlib.h>

/** This function syncs the two given pages, copying the page with the wrong
 * CRC into the page with the correct one. */
void config_sync_pages(void *page1, void *page2, size_t page_size);

/** Returns true if the given config page is valid. */
bool config_is_valid(void *page, size_t page_size);


#ifdef __cplusplus
}
#endif

#endif
