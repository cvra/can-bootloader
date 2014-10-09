# Bootloader protocol

## Design goals

The bootloader protocol must be able to run over UART (point to point) or CAN (using adressing).
Running the bootloader on UART allows for easier testing since the bootloader can be tested when connected directly to a PC.
It also allows the usage of the bootloader in other projects which can be useful and increases testing of the bootloader.

When running on top of CAN, it must work with UAVCAN, that means it can not use extended CAN frames and must gracefully handle lost packets.

## CAN Transport layer
Apparently it will not be really needed to have a complicated transport layer here.
Using standard frames over extended frames guarantees that the bootloader protocol always win the arbitration.
CAN is pretty robust so packet drops will be really infrequent and will be detected when doing the CRC of the whole flash.
We will never send packet out of order so no sequence number is needed.

The first bit is the unicast / multicast bit.
If this bit is zero, then the message is unicast to the Node ID.
If the bit is one, then the message is multicast to the Group ID

The format of the CAN message ID is really simple :

* 1 bit for unicast / multicast.
* 7 bits for the Node/Group ID (same number as UAVCAN)
* 3 reserved

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
The command and its parameters are written in a MessagePack array so we can know the command count.
Some commands will require an answer for example when writing the application CRC back to the programmer.
They should simply send the MessagePack encoded response on the bus.

## Standard commands

* Jump to application (0x01). No parameters. Simply starts the application code.
* CRC flash region (0x02). 2 parameters : start and end adress of the region we want to check. Returns the CRC32 of this region.
* Write flash (0x03). Parameters : Start adress and sequence of bytes to write. Returns CRC32 of the written data.
* Read flash (0x04). Parameters : Start adress and length. Returns sequence of read bytes

# Flash layout
The bootloader resides in the N flash pages.
It is followed by one page of bootloader config page.
This page contains the following informations, stored as a messagepack map.
* nodeID: Unique node identifier, ranging from 1 to 127.
* name: Human readable name describing the board (ex: "arms.left.shoulder").
* model: Board model (ex: "CVRA.MotorController.v1")
* crcApp: Application CRC. If the CRC matches the bootloader will automatically boot into it after a timeout.
* updateCnt: Firmware update counter. Used for diagnostics and lifespan estimation.
* groups: Array containing the various multicast groups this board must listen to.

Additional informations are stored in the bootloader binary :
* Git commit SHA
* Build date

After the bootloader and its config page comes the application.
Application flash layout is out of the scope of this document.

# References
[1] MessagePack specifications : https://github.com/msgpack/msgpack/blob/master/spec.md

