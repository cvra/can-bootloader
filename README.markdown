# Bootloader protocol
[![Build Status](https://travis-ci.org/cvra/can-bootloader.svg)](https://travis-ci.org/cvra/can-bootloader)
# Design goals

The bootloader protocol must be able to run over UART (point to point) or CAN (using adressing).
Running the bootloader on UART allows for easier testing since the bootloader can be tested when connected directly to a PC.
It also allows the usage of the bootloader in other projects which can be useful and increases testing of the bootloader.

When running on top of CAN, it must work with UAVCAN, that means it can not use extended CAN frames and must gracefully handle lost packets.

# CAN Transport layer
Apparently it will not be really needed to have a complicated transport layer here.
Using standard frames over extended frames guarantees that the bootloader protocol always win the arbitration.
CAN is pretty robust so packet drops will be really infrequent and will be detected when doing the CRC of the whole flash.
We will never send packet out of order so no sequence number is needed.

Multicast is done by having a list of ID who are adressed at the beginning of a datagram.
Unicast is just a special case of multicast with only one node in the list.

There is one bit to indicate if this message is the first of a datagram (1) or if it is following a start marker (0).

The format of the CAN message ID is :

* bits 10..8: 3 reserved bits, set to zero for bootloader frames
* bit 7: 1 bit for start of datagram bit (1 if first frame in datagram, 0 otherwise)
* bits 6..0: bits for the source ID

*Note:* The first 3 bits of the ID are dominant (0) for bootloader frames. It has therefore highest priority on the bus.

## CAN Datagram format
The CAN datagram layer has the following resposibilities :
* Adressing
* Ensure data integrity (CRC)

The datagram format is the following :

1. Protocol version (currently 0x01): 1 byte
2. CRC32 of the whole datagram : 4 bytes
3. Destination ID list length (m) : 1 byte
4. Destination IDs : m bytes
5. Data length : 4 bytes, MSB first
6. Data: n bytes

# UART Transport layer
Just send the bytes at 115200 bauds, 8 bit, no parity.

## UART Datagram format
The datagram layer has the following responsibilities :
* Find start and end of a datagram
* Ensure data integrity (CRC)

The packet format is excessively simple :

1. START marker: 1 byte
2. Length of the data (n): 2 bytes
3. CRC32 of the data
3. Data (n bytes)

The data field is escaped so a START byte is replaced by ESC ESC_START and an ESC byte is replaced by ESC ESC_ESC.

| Hex value | Abbreviation | Description
|-----------|--------------|------------
| 0xC0      | START        | Datagram start
| 0xDB      | ESC          | Escape
| 0xDC      | ESC_START    | Transposed Frame start
| 0xDD      | ESC_ESC      | Transposed Frame Escape

# Command format

The command format is simple :

    +-------+------+---+-------+-------+
    |Version|Command|Param1|...|ParamN |
    +-------+------+---+-------+-------+

The protocol version is simply an integer that increments everytime a change in the command set is done.
The command interpreter silently ignores commands with the wrong version number to avoid misinterpreting packets.
Command and parameters are encoded using MessagePack [1] because it is efficient and extendable.
The command and its parameters are written in a MessagePack array so we can know the command count.
Some commands will require an answer for example when writing the application CRC back to the programmer.
They should simply send the MessagePack encoded response on the bus.

## Standard commands

1. Jump to application (0x01). No parameters. Simply starts the application code.
2. CRC flash region (0x02). 2 parameters : start adress and length of the region we want to check. Returns the CRC32 of this region.
3. Erase flash page (0x03). Parameters : Page address, device class (string). Returns nothing.
4. Write flash (0x04). Parameters : Start adress, device class (string) and sequence of bytes to write. Returns nothing.
5. Ping (0x05). Parameters: None. Returns: True if bootloader is ready to accept a command.
6. Read flash (0x06). Parameters : Start adress and length. Returns sequence of read bytes
7. Update config (0x07). The only parameters is a MessagePack map containing the configuration values to update. If a config value is not in its parameters, it will not be changed.
8. Save config to flash.

*Note:* Adresses (pointers) in the arguments are represented as 64 bits integers.
64 bits was chosen to allow tests to run on 64 bits platforms too.

## Multicast write
When using multicast write the recommended way is the following :

1. Write to all board using multicast write command (0x04).
2. Wait for one board to reply with 'True'
3. Poll every board write status, wait until every board has finished.
4. Ask each board to compute the CRC of the page you just wrote. If a board is wrong, reflash just this one.

# Flash layout
The bootloader resides in the N flash pages.
It is followed by two pages of bootloader config.
The two configuration pages are here for redundancy and are checked by a CRC32 placed at the beginning (see `cvra/serializer` for details).
If one page CRC does not match, then the bootloader will copy the other into it at boot.
When updating the config, it should be CRC checked before writing to the redundancy page.

The config contains the following informations, stored as a messagepack map.
* ID: Unique node identifier, ranging from 1 to 127.
* name: Human readable name describing the board (ex: "arms.left.shoulder"). Max length: 64
* device_class: Board model (ex: "CVRA.MotorController.v1"). Max length: 64
* application_crc: Application CRC. If the CRC matches the bootloader will automatically boot into it after a timeout.
* application_size: Needed for CRC calculation.
* update_count: Firmware update counter. Used for diagnostics and lifespan estimation.

Additional informations are stored in the bootloader binary :
* Git commit SHA
* Build date

After the bootloader and its config page comes the application.
Application flash layout is out of the scope of this document.

# Performance considerations
Assuming :
* CAN speed is 1 Mb/s
* CAN overhead is about 50%
* Protocol overhead + data drop is about 10%. Keep in mind that size of a write chunk might affect this since CRC checksum is done after each chunk.
* Binary size : 1 MB
* The bottleneck is in the CAN network, not in the CRC computation or in the flash write speed.
* The time to check the CRC of each board can be neglected.
* We use multicast write commands to lower bandwith usage.

We can flash a whole board (1MB) in about 20 seconds.
If all board in the robot run the same firmware, the whole robot can be updated in about the same time, which is pretty good.

# Safety features
The bootloader is expected to be one of the safest part of the robot firmware.
Correcting a bug in the bootloader could be very complicated, requiring disassembly of the robot in the worst cases.
Therefore, when implementing the bootloader or the associated protocol, the following safety points must be taken into account:
* The bootloader must *never* erase itself or its configuration page.
* It should never write to flash if the device class does not match. Doing so might result in the wrong firmware being written to the board, which is dangerous.
* If the application CRC does not match, the bootloader should not boot it.
* On power up the bootloader should wait enough time for the user to input commands before jumping to the application code.

# References
[1] MessagePack specifications : https://github.com/msgpack/msgpack/blob/master/spec.md

