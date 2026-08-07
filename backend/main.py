import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from auth import COOKIE_NAME, UserManager, UserDatabase, password_helper, resolve_session
from database import AsyncSessionLocal, engine, get_db, IMAGES_DIR, Base
import models  # noqa: F401 — ensures models are registered
from migrate import run_migrations
from models import User
from routers import auth, items, locations, search, drinks, tally, notes, shopping, users, groups, einstellungen

log = logging.getLogger("uvicorn.error")

# Frontend liegt ausserhalb von backend/ -- realpath aufloesen, damit der
# Traversal-Schutz weiter unten mit einem echten absoluten Pfad vergleicht.
FRONTEND_DIST = os.path.realpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend", "dist")
)

# Diese Pfade sind ohne Anmeldung erreichbar -- mehr nicht.
PUBLIC_API_PATHS = {"/api/auth/login", "/api/auth/register"}


async def bootstrap_admin() -> None:
    """Legt den Admin aus der .env an, falls er noch nicht existiert.

    Existiert er bereits, wird sein Passwort auf den Wert aus der .env
    gesetzt -- so kommst du wieder rein, falls du dich aussperrst.
    """
    username = os.environ.get("ADMIN_USER")
    password = os.environ.get("ADMIN_PASSWORD")
    if not username or not password:
        log.warning(
            "ADMIN_USER/ADMIN_PASSWORD nicht gesetzt - es wird kein Admin angelegt. "
            "Ohne Admin kann niemand Registrierungen freigeben."
        )
        return

    async with AsyncSessionLocal() as session:
        manager = UserManager(UserDatabase(session, User), password_helper)
        existing = await manager.user_db.get_by_username(username)
        if existing is None:
            await manager.register(
                username=username,
                display_name=os.environ.get("ADMIN_DISPLAY_NAME", username),
                password=password,
                is_active=True,
                is_superuser=True,
            )
            log.info("Admin '%s' aus der .env angelegt.", username)
        else:
            await manager.user_db.update(existing, {
                "hashed_password": manager.password_helper.hash(password),
                "is_active": True,
                "is_superuser": True,
            })
            log.info("Admin '%s' aktualisiert (Passwort aus der .env gesetzt).", username)


@asynccontextmanager
async def lifespan(app: FastAPI):
    for change in run_migrations(engine):
        log.info("Migration: %s", change)
    Base.metadata.create_all(bind=engine)
    await bootstrap_admin()
    yield


app = FastAPI(title="Bauwagen DB", version="2.0.0", lifespan=lifespan)


def _is_public(path: str) -> bool:
    """Default-Deny: alles was Daten liefert braucht eine Anmeldung.

    Oeffentlich bleibt nur, was der Browser braucht *um* die Loginseite
    ueberhaupt anzuzeigen: das gebaute JS/CSS-Bundle und die Icons. Die
    liegen ohnehin bei jedem Besucher im Cache und enthalten keine Daten.
    """
    if path in PUBLIC_API_PATHS:
        return True
    if path.startswith("/api/") or path.startswith("/images/"):
        return False
    return True


def _sitzung_pruefen(token: str | None):
    """Laeuft in einem Arbeitsthread, nicht im Event-Loop.

    SQLite-Zugriffe sind blockierend. Direkt im Loop ausgefuehrt haben sie
    unter Last zu einer Verklemmung gefuehrt: ab etwa 20 gleichzeitigen
    Anfragen war der Verbindungspool leer, die Middleware wartete im Loop
    auf eine freie Verbindung -- und die konnte nicht frei werden, weil
    dafuer der Loop weiterlaufen muesste. Ergebnis: die Anfragen blieben
    haengen. Statische Pfade waren nie betroffen, weil sie hier nicht
    hereinlaufen.
    """
    db = next(get_db())
    try:
        return resolve_session(db, token)
    finally:
        db.close()


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    request.state.user = None
    path = request.url.path

    # Nur fuer Anfragen aufloesen, die einen Benutzer brauchen -- sonst
    # wuerde jede JS-, CSS- und Icon-Datei eine DB-Abfrage ausloesen.
    needs_user = path.startswith("/api/") or path.startswith("/images/")

    if needs_user:
        request.state.user = await run_in_threadpool(
            _sitzung_pruefen, request.cookies.get(COOKIE_NAME)
        )

        if not _is_public(path) and request.state.user is None:
            return JSONResponse({"detail": "Nicht angemeldet"}, status_code=401)

    return await call_next(request)


# API routes
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(groups.router, prefix="/api")
app.include_router(einstellungen.router, prefix="/api")
app.include_router(items.router, prefix="/api")
app.include_router(locations.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(drinks.router, prefix="/api")
app.include_router(tally.router, prefix="/api")
app.include_router(notes.router, prefix="/api")
app.include_router(shopping.router, prefix="/api")

# Serve uploaded images (durch die Middleware oben geschuetzt)
app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")

# Serve frontend (compiled Vue app)
if os.path.isdir(FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")

    # Diese Dateien duerfen NIE gecacht werden. Der Service Worker steuert
    # das Update aller uebrigen Dateien -- liegt er im Cache (bei uns:
    # Cloudflare cachte ihn wegen der .js-Endung 4 Stunden), bekommen die
    # Geraete die neue Version nie zu sehen. Die Dateien unter /assets/
    # tragen dagegen einen Hash im Namen und duerfen dauerhaft gecacht werden.
    NO_CACHE_FILES = {"sw.js", "registerSW.js", "index.html", "manifest.webmanifest"}
    NO_CACHE_HEADERS = {"Cache-Control": "no-cache, no-store, must-revalidate"}

    def _file_response(path: str) -> FileResponse:
        if os.path.basename(path) in NO_CACHE_FILES:
            return FileResponse(path, headers=NO_CACHE_HEADERS)
        return FileResponse(path)

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend(full_path: str):
        index = os.path.join(FRONTEND_DIST, "index.html")
        if not full_path:
            return _file_response(index)

        # os.path.join alleine reicht nicht: "../../data/storage.db" wuerde
        # sonst aus dem dist-Verzeichnis herausfuehren.
        candidate = os.path.realpath(os.path.join(FRONTEND_DIST, full_path))
        inside_dist = candidate == FRONTEND_DIST or candidate.startswith(FRONTEND_DIST + os.sep)

        if inside_dist and os.path.isfile(candidate):
            return _file_response(candidate)

        # Unbekannter Pfad -> SPA laedt und entscheidet selbst (z.B. /items/5)
        return _file_response(index)
