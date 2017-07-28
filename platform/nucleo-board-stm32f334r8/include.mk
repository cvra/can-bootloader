

PACKAGER_INCDIR += ././

PACKAGER_INCDIR += dependencies/



ASMSRC += ./platform/mcu/armv7-m/boot.s

CSRC += ./platform/mcu/armv7-m/boot_arg.c

CSRC += ./platform/mcu/armv7-m/timeout_timer.c

CSRC += ./platform/mcu/armv7-m/vector_table.c

CSRC += ./platform/mcu/stm32f3/can_interface.c

CSRC += ./platform/mcu/stm32f3/flash_writer.c

CSRC += ./bootloader.c

CSRC += ./can_datagram.c

CSRC += ./command.c

CSRC += ./config.c

CSRC += ./dependencies/cmp/cmp.c

CSRC += dependencies/cmp_mem_access/cmp_mem_access.c

CSRC += dependencies/crc/crc32.c
