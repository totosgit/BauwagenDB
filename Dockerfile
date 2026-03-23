# Stage 1: Frontend bauen
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Produktions-Image
FROM python:3.12-slim
WORKDIR /app

# Python-Abhängigkeiten installieren
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Backend-Code kopieren
COPY backend/ ./backend/

# Gebautes Frontend kopieren
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Data-Verzeichnis anlegen (wird als Volume gemountet)
RUN mkdir -p /app/data/images

EXPOSE 8000

WORKDIR /app/backend
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
