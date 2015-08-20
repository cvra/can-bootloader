# Steps to build the bootloader binary

run the packager:

```
python3 ../packager/packager.py
```

build libopencm3:

```
cd libopencm3
make
cd ..
```

build the desired platform (eg. motor board):

```
cd platform/motor-board-v1
make
```

to flash, simply run ```make flash``` from the platform directory
