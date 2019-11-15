#ifndef CONFIG_H
#define CONFIG_H

#ifdef __cplusplus
extern "C" {
#endif

#include <stdlib.h>
#include <stdbool.h>
#include <cmp/cmp.h>

typedef struct {
    uint8_t ID; /**< Node ID */
    char board_name[64 + 1]; /**< Node human readable name, eg: 'arms.left.shoulder'. */
    char device_class[64 + 1]; /**< Node device class example : 'CVRA.motorboard.v1'*/
    uint32_t application_crc;
    uint32_t application_size;
    uint32_t update_count;
} bootloader_config_t;

/** Returns true if the given config page is valid. */
bool config_is_valid(void* page, size_t page_size);

/** Serializes the configuration to the buffer.
 *
 * It must be done on a RAM buffer because we will modify it non sequentially, to add CRC.
 */
void config_write(void* buffer, bootloader_config_t* config, size_t buffer_size);

/** Serializes the config into a messagepack map. */
void config_write_messagepack(cmp_ctx_t* context, bootloader_config_t* config);

bootloader_config_t config_read(void* buffer, size_t buffer_size);

/** Updates the config from the keys found in the messagepack map.
 *
 * @note Keys not in the MessagePack map are left unchanged.
 */
void config_update_from_serialized(bootloader_config_t* config, cmp_ctx_t* context);

#ifdef __cplusplus
}
#endif

#endif
