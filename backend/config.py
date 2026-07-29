"""Laedt die .env aus dem Projektverzeichnis.

Im Container uebernimmt das docker-compose ueber `env_file`. Beim lokalen
Start passiert das aber nicht -- ohne diese Datei waeren ADMIN_USER und
ADMIN_PASSWORD dann nicht gesetzt und es wuerde gar kein Admin angelegt.

Wird von database.py importiert, also bevor irgendein anderes Modul
os.environ ausliest. Bereits gesetzte Umgebungsvariablen gewinnen
(load_dotenv ueberschreibt nichts), damit man beim Start gezielt etwas
anderes mitgeben kann.
"""
import os

from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, "..", ".env")

load_dotenv(ENV_PATH)
