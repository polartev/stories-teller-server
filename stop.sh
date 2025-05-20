#!/bin/bash

PID_FILE=~/stories-teller/server.pid

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null; then
        echo "Stopping process $PID"
        kill $PID
        rm "$PID_FILE"
    else
        echo "No running process found with PID $PID"
        rm "$PID_FILE"
    fi
else
    echo "PID file not found"
fi