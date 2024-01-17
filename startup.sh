#!/bin/bash
amixer sset Master 60%
cd /home/dewdrop/player
. venv/bin/activate
python3 main.py