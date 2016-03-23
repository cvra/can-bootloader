# Bootloader client

This repository contains the code for the client running on the host.
In the end it will be able to update the whole robot using a CAN to serial link.
The serial stream can be implemented over a standard UART connexion or a TCP stream.

# Installation
Here we install dependencies in a virtual environment to avoid cluttering system install.
An alternative way is to use your system package manager to install dependencies.
Installing system wide packages via pip is *not a good idea*.

```sh
# Create virtual env
virtualenv --python=python3 venv
source env/bin/activate

# if you use fish, run this instead:
# source env/bin/activate.fish

# Install required packages
python setup.py install
```

## Development mode
If you are working on the bootloader client code you might want to use `python setup.py develop`.
Instead of copying the code into the python path it symlinks it, meaning you can edit your code and run the modified version without running `setup.py` again.

To run the tests, run `python -m unittest discover` after installing the dependencies.

# Builtin tools
These are the tools for talking with the bootloader on the host.
They can all run with `-h/--help`, so use that to know how arguments works.

* `bootloader_flash`: Used to program target boards.
* `bootloader_read_config`: Used to read the config from a bunch of boards and dump it as JSON.
* `bootloader_change_id`: Used to change a single device ID *Use it carefully.*
* `bootloader_write_config`: Used to change board config, such as device class, name and so on.
