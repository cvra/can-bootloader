#ifndef BOOT_ARG_H
#define BOOT_ARG_H

#ifdef __cplusplus
extern "C" {
#endif

#include <stdint.h>

#define BOOT_ARG_START_BOOTLOADER 0x00
#define BOOT_ARG_START_BOOTLOADER_NO_TIMEOUT 0x01
#define BOOT_ARG_START_APPLICATION 0x02
#define BOOT_ARG_START_ST_BOOTLOADER 0x03

void reboot_system(uint8_t arg);

#ifdef __cplusplus
}
#endif

#endif // BOOT_ARG_H
