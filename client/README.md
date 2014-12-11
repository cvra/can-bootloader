# Bootloader client

This repository contains the code for the client running on the host.
In the end it will be able to update the whole robot using a CAN to serial link.
The serial stream can be implemented over a standard UART connexion or a TCP stream.

# Code organization

The system aims to be flexible: it should be possible to replace the serial bridge with a PCI CAN adapter without too much rewriting.
This implies that there is a few different level of encapsulations:

1. At the top sits the bootloader protocol (`commands.py`)
2. Immediately below is the CAN datagram layers.
    Its role is to encapsulate a stream of bytes, adding a CRC and adressing system.
3. The CAN datagram is then cut into chunks small enough to fit in a single CAN frame.
    The id of each frame is also added at this step.
4. Each CAN frame is converted into a command for the CAN-serial bridge protocol (`can_uart.py`).
5. Each bridge command is encapsulated in a single serial datagram (`uart_datagrams.py`).
6. Encoded datagrams can now be sent on the serial link.

Translating this into code gives the following:

```py
import can, commands, uart_datagrams, can_uart

# Data to write to flash
data = "Hello, world!".encode('ascii')

# Generates the command
data = commands.encode_write_flash(data=data, adress=0x00, device_class="dummy")

# Encapsulates it in a CAN datagram
data = can.encode_datagram(data=data, destinations=[1])

# Slice the datagram in frames
frames = can.datagram_to_frames(data, source=0)

# Serializes CAN frames for the bridge
frames = [can_uart.encode_frame(f) for f in frames]

# Packs each frame in a serial datagram
frames = [uart_datagrams.datagram_encode(f) for f in frames]

# Flattens the list of UART datagram frames to a stream of byte
data = [c for f in frames for c in f]

# Print can be replace with anything (socket write, serial port, etc..)
print(data)
```

