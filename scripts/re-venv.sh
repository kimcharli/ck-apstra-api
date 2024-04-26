#!/bin/bash

if [ -x ${VIRTUAL_ENV+x} ]
then
    echo "VIRTUAL_ENV is unser"
else
    echo "Deactivating existing virtual environment"
    deactivate
fi
rm -rf .venv
uv venv
source .venv/bin/activate
uv pip install -e .
