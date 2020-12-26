#!/usr/bin/env bash

# Make the script fail if any command in it fail
set -e

if [ "$BUILD_TYPE" == "" ]
then
    echo "Please define \$BUILD_TYPE!"
    exit 1
fi

source env/bin/activate
export PATH=$HOME/gcc-arm-none-eabi/bin/:$PATH

export CFLAGS="$CFLAGS -I $HOME/cpputest/include/"
export CXXFLAGS="$CXXFLAGS -I $HOME/cpputest/include/"
export LDFLAGS="$CXXFLAGS -L $HOME/cpputest/lib/"

packager

case $BUILD_TYPE in
    tests)
        mkdir build
        cd build
        cmake ..
        make
        ./tests
        ;;

    client-tests)
        cd client/
        python -m unittest discover
        ;;

    *)
        echo "Unknown build type $BUILD_TYPE"
        exit 1
        ;;
esac
