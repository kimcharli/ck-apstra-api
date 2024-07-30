#!/bin/bash

if [ -x ${VIRTUAL_ENV+x} ]
then
    echo "VIRTUAL_ENV is unset"
else
    echo "Deactivating existing virtual environment"
    deactivate
fi
rm -rf .venv
find src -name __pycache__ -exec rm -rf {} \;
uv venv
source .venv/bin/activate
uv pip install -e .
