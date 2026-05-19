#!/bin/bash
cd "$(dirname "$0")"
echo "🚀 Arrancando backend..."
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
