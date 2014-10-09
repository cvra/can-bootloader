# Bootloader protocol

## Design goals

* The bootloader protocol must be able to run over UART (point to point) or CAN (using adressing).
* When running on top of CAN, it must work with UAVCAN, that means it can not use extended CAN frames and must gracefully handle lost packets.

## CAN Transport layer
Apparently it will not be really needed to have a complicated transport layer here.
Using standard frames over extended frames guarantees that the bootloader protocol always win the arbitration.
CAN is pretty robust so packet drops will be really infrequent and will be detected when doing the CRC of the whole flash.
We will never send packet out of order so no sequence number is needed.

The format of the CAN message ID is really simple :

* Uses CAN standard frames
* 7 MSBs are for the Node ID (same number as UAVCAN)
* The 4 LSBs are reserved

## UART Transport layer
Just send the bytes at 115200 bauds, 8 bit, no parity.

## Datagram format
Since we want to transmit over CAN (message oriented) and over UART (stream oriented), we will encapsulate datas into datagrams.

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

## Command format

The command format is simple :

    +-------+------+---+-------+
    |Command|Param1|...|ParamN |
    +-------+------+---+-------+

Command and parameters are encoded using MessagePack [1] because it is efficient and extendable.
Some commands will require an answer for example when writing the application CRC back to the programmer.
They should simply send the MessagePack encoded response on the bus.


# Various bootloader design ideas
* Boards always boot into bootloader mode and then a command from the master is needed to jump to application code. We cannot jump to bootloader from application code because we want to be absolutely sure that we can always access it.
* A global checksum of the flash (minus bootloader and configuration pages) is needed to ensure integrity.

# References
[1] MessagePack specifications : https://github.com/msgpack/msgpack/blob/master/spec.md

