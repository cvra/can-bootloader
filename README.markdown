# Bootloader protocol

## Design goals

* The bootloader protocol must be able to run over UART (point to point) or CAN (using adressing).
* When running on top of CAN, it must work with UAVCAN, that means it can not use extended CAN frames and must gracefully handle lost packets.
* Time for flashing a full 128k of flash should stay under one second which means the protocol should not have too much overhead.

## CAN Transport layer

Lost packet handling is really simple.
It is based on the following ideas :

1. Each packet contains a sequence number directly embedded in the message ID.
2. Since we use the same node id for UAVCAN and for the bootloader that means 7 bits for the Node ID.
3. When the sequence number reaches max value (0x8) the sequence number becomes zero again ONLY IF packet with sequence number zero has been ACKd.
4. When a node receives a packet it must ACK the packet if the sequence number is the expected one. Otherwise it must send a NACK for the expected sequence number.
5. If a node receives a NACK packet, it must retransmit the given packet AND all the following ones. Out of order arrival of packet is not handled.

An ack / nack packet is simply a packet with the ack bit in the message id set to one.
If the packet data (lenght = 1 byte) is 0 then it is an ACK, otherwise it is a NACK.
This allows various NACK error code to be transmitted in the same packet.

## UART Transport layer
TODO (really needed ?)

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


# Various bootloader design ideas
* Boards always boot into bootloader mode and then a command from the master is needed to jump to application code. We cannot jump to bootloader from application code because we want to be absolutely sure that we can always access it.
* A global checksum of the flash (minus bootloader and configuration pages) is needed to ensure integrity.

# References
[1] MessagePack specifications : https://github.com/msgpack/msgpack/blob/master/spec.md

