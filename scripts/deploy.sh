#!/bin/bash

if ! [[ -d ./venv ]]; then
    python3 -m venv venv
    pip install -U discord.py
fi

source ./venv/bin/activate
python3 ./main.py

