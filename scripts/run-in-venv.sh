#! /bin/bash

python -m venv .venv
source .venv/bin/activate && python -m pip install -r converter/requirements.txt

source .venv/bin/activate && $@