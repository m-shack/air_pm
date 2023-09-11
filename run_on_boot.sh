#!/bin/bash
#File: run_on_boot.sh

# Absolute path to Virtual Environment python interpreter
PYTHON=/home/pi/air_pm/venv/bin/python

LOG=/home/pi/air_pm/crash_info.log

# Absolute path to Python script
SCRIPT=/home/pi/air_pm/datalog_pa3.py

$PYTHON $SCRIPT >> $LOG 2>&1
