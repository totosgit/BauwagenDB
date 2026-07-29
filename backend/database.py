import config  # noqa: F401 — laedt die .env, muss vor allen os.environ-Zugriffen passieren

from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
IMAGES_DIR = os.path.join(DATA_DIR, "images")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

DB_FILE = os.path.join(DATA_DIR, "storage.db")
DATABASE_URL = f"sqlite:///{DB_FILE}"
# fastapi-users arbeitet ausschliesslich async. Statt die bestehenden Router
# alle umzuschreiben, laeuft eine zweite (async) Engine auf derselben Datei --
# dank WAL vertragen sich die beiden Verbindungen problemlos.
ASYNC_DATABASE_URL = f"sqlite+aiosqlite:///{DB_FILE}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
async_engine = create_async_engine(ASYNC_DATABASE_URL, connect_args={"check_same_thread": False})

# Enable WAL mode for better concurrent access
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

event.listens_for(engine, "connect")(set_sqlite_pragma)
event.listens_for(async_engine.sync_engine, "connect")(set_sqlite_pragma)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = async_sessionmaker(async_engine, expire_on_commit=False)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db():
    async with AsyncSessionLocal() as session:
        yield session
