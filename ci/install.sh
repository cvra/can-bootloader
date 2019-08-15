#!/usr/bin/env bash

# Make the script fail if any command in it fail
set -e

python3.5 -m venv env --without-pip
source env/bin/activate
python --version
wget https://bootstrap.pypa.io/get-pip.py
python get-pip.py
pip install cvra-packager~=1.0.0

case $BUILD_TYPE in
    build)
        pushd $HOME
        wget https://developer.arm.com/-/media/Files/downloads/gnu-rm/8-2018q4/gcc-arm-none-eabi-8-2018-q4-major-linux.tar.bz2 -O arm-gcc-linux.tar.bz2
        tar -xf arm-gcc-linux.tar.bz2

        mv gcc-arm-none-eabi-* gcc-arm-none-eabi

        popd
        ;;

    tests)
        # Install cpputest
        pushd ..
        wget "https://github.com/cpputest/cpputest/releases/download/v3.8/cpputest-3.8.tar.gz" -O cpputest.tar.gz
        tar -xzf cpputest.tar.gz
        cd cpputest-3.8/
        ./configure --prefix=$HOME/cpputest
        make
        make install
        popd
        ;;

    client-tests)
        pushd client
        python setup.py install
        popd
        ;;

    *)
        echo "Unknown build type $BUILD_TYPE"
        exit 1
        ;;
esac
