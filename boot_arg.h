#ifndef BOOT_H
#define BOOT_H

#define BOOT_ARG_APP_START  0x00
#define BOOT_ARG_APP_UPDATE 0x01
#define BOOT_ARG_SAFE_MODE  0x03

void reboot(int boot_arg);

#endif // BOOT_H
