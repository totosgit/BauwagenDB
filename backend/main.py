import os
from datetime import datetime, timedelta

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from database import engine, IMAGES_DIR, Base
import models  # noqa: F401 — ensures models are registered
from models import Session
from database import get_db
from routers import items, locations, search, drinks, tally
from routers import auth

SESSION_DAYS = 7
COOKIE_NAME = "session"

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Bauwagen DB", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    path = request.url.path

    # Auth-Endpunkte und alles außer /api/ sind frei zugänglich
    if not path.startswith("/api/") or path.startswith("/api/auth/"):
        return await call_next(request)

    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return JSONResponse({"detail": "Nicht eingeloggt"}, status_code=401)

    db = next(get_db())
    try:
        session = db.get(Session, token)
        if not session or session.expires_at < datetime.utcnow():
            if session:
                db.delete(session)
                db.commit()
            return JSONResponse({"detail": "Sitzung abgelaufen"}, status_code=401)

        # Sliding: Ablaufzeit verlängern
        session.expires_at = datetime.utcnow() + timedelta(days=SESSION_DAYS)
        db.commit()
    finally:
        db.close()

    response = await call_next(request)
    response.set_cookie(
        COOKIE_NAME, token,
        httponly=True,
        max_age=SESSION_DAYS * 86400,
        samesite="lax",
    )
    return response


# API routes
app.include_router(auth.router, prefix="/api")
app.include_router(items.router, prefix="/api")
app.include_router(locations.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(drinks.router, prefix="/api")
app.include_router(tally.router, prefix="/api")

# Serve uploaded images
app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")

# Serve frontend (compiled Vue app)
FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend(full_path: str):
        index = os.path.join(FRONTEND_DIST, "index.html")
        return FileResponse(index)
