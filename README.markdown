# Bootloader protocol

![Python tests](https://github.com/cvra/can-bootloader/workflows/Python%20tests/badge.svg)

![Unit tests](https://github.com/cvra/can-bootloader/workflows/Unit%20tests/badge.svg)

![STM32 builds](https://github.com/cvra/can-bootloader/workflows/STM32%20builds/badge.svg)

This repository contains the code used for the bootloader running on every microcontroller in our robots.
It allows us to quickly update the firmware on all (>20) boards quickly and without disassembly or additional electrical connections.

# Config pages

The bootloader code is followed by two pages of bootloader config.
The two pages are for redundancy and are checked by a CRC32 placed at the beginning of a page.
The bootloader checks the configuration CRC at boot.
If an invalid page is detected, its content is replaced by the redundant page.

After the bootloader has updated one of the two configuratio pages, it verifies it before proceeding to the second one.
This ensures that there is always a valid configuration page to prevent bricking a board.

The config contains the following informations, stored as a messagepack map:

* ID: Unique node identifier, ranging from 1 to 127.
* name: Human readable name describing the board (ex: "arms.left.shoulder"). Max length: 64
* device_class: Board model (ex: "CVRA.MotorController.v1"). Max length: 64
* application_crc: Application CRC. If the CRC matches the bootloader will automatically boot into it after a timeout.
* application_size: Needed for CRC calculation.
* update_count: Firmware update counter. Used for diagnostics and lifespan estimation.

# Performance considerations

Assuming :

* CAN speed is 1 Mb/s
* CAN overhead is about 50%
* Protocol overhead + data drop is about 10%.
    The size of a write chunk might affect this since invalid data is dropped by chunk.
* Binary size : 1 MB
* The bottleneck is in the CAN network, not in the CRC computation or in the flash write speed.
* The time to check the CRC of each board can be neglected.
* We use multicast write commands to lower bandwith usage.

We can flash a whole board (1MB) in about 20 seconds.
If all board in the robot run the same firmware, this is the time required to do a full system update!

# Safety features
The bootloader is expected to be one of the safest part of the robot firmware.
Correcting a bug in the bootloader could be very complicated, requiring disassembly of the robot in the worst cases.
Therefore, when implementing the bootloader or the associated protocol, the following safety points must be taken into account:

* The bootloader must *never* erase itself or its configuration page.
* It should never write to flash if the device class does not match. Doing so might result in the wrong firmware being written to the board, which is dangerous.
* If the application CRC does not match, the bootloader should not boot it.
* On power up the bootloader should wait enough time for the user to input commands before jumping to the application code.

# Building

1. Run [CVRA's packager script](https://github.com/cvra/packager): `packager`.
2. Build libopencm3: `pushd libopencm3 && make && popd`.
3. Build your desired platform: `cd platform/motor-board-v1 && make`.
4. Flash the resulting binary to your board: `make flash`.
