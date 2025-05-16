#!/bin/bash
source ~/stories-teller/venv/bin/activate
nohup uvicorn app.main:app --host 127.0.0.1 --port 8000 > ~/stories-teller/server.log 2>&1 &