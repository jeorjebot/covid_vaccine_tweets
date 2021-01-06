#!/bin/sh

# automatic reconnection within 5 seconds
while true; do
    python3 stream.py
    sleep 5
done