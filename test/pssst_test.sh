#!/bin/bash
set -o errexit

if [ ! -f pssst.py ]; then
    ln -s ../src/cli/pssst.py
fi

python pssst_test.py $*
