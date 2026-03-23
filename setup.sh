#!/bin/bash
set -e

echo "=== Bauwagen DB Setup ==="

# Backend
echo "→ Python venv einrichten ..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt

# Frontend
echo "→ Node dependencies installieren ..."
cd frontend
npm install
echo "→ Frontend bauen ..."
npm run build
cd ..

echo ""
echo "✓ Setup abgeschlossen!"
echo "  Starten mit: ./start.sh"
