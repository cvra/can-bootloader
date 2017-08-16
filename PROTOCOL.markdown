# Bootloader protocol

## Design goals

* The bootloader might coexist with higher level protocols (UAVCAN) and its operation must not be disturbed.
* It must handle lost CAN frames gracefully.
* The protocol must be open to extension.

## CAN Transport layer
It will not be really needed to have a complicated transport layer here.
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
3. Erase flash page (0x03). Parameters : Page address, device class (string). Returns: True if successful.
4. Write flash (0x04). Parameters : Start adress, device class (string) and sequence of bytes to write. Returns: True if successful.
5. Ping (0x05). Parameters: None. Returns: True if bootloader is ready to accept a command.
6. Read flash (0x06). Parameters : Start adress and length. Returns sequence of read bytes
7. Update config (0x07). The only parameters is a MessagePack map containing the configuration values to update. If a config value is not in its parameters, it will not be changed. Returns: True if successful.
8. Save config to flash (0x08). Returns: True if successful.
9. Read current config (0x09). No parameters. Writes back a messagepack map containing the bootloader config.

*Note:* Adresses (pointers) in the arguments are represented as 64 bits integers.
64 bits was chosen to allow tests to run on 64 bits platforms too.

## Multicast write
When using multicast write the recommended way is the following :

1. Write to all boards using multicast write command.
2. Wait with a timeout for the command to finish.
3. Continue only with boards that successfully finished.
4. Verify the written data via CRC command.
5. Reflash the boards that failed during above process. (optional)

# References
[1] MessagePack specifications : https://github.com/msgpack/msgpack/blob/master/spec.md
