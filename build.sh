#!/bin/bash
set -e

. venv/bin/activate
# build single binary
pyinstaller --onefile cli.py