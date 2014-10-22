#ifndef CONFIG_H
#define CONFIG_H

#ifdef __cplusplus
extern "C" {
#endif

#include <stdlib.h>

typedef struct {
    uint8_t ID; /**< Node ID */
    char board_name[64 + 1];   /**< Node human readable name, eg: 'arms.left.shoulder'. */
    char device_class[64 + 1]; /**< Node device class example : 'CVRA.motorboard.v1'*/
    uint32_t application_crc;
} bootloader_config_t;

/** This function syncs the two given pages, copying the page with the wrong
 * CRC into the page with the correct one. */
void config_sync_pages(void *page1, void *page2, size_t page_size);

/** Returns true if the given config page is valid. */
bool config_is_valid(void *page, size_t page_size);

/** Serializes the configuration to the buffer.
 *
 * It must be done on a RAM buffer because we will modify it non sequentially, to add CRC.
 */
void config_write(void *buffer,  bootloader_config_t config, size_t buffer_size);

bootloader_config_t config_read(void *buffer, size_t buffer_size);

#ifdef __cplusplus
}
#endif

#endif
