import os
import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Response, Cookie
from pydantic import BaseModel
from sqlalchemy.orm import Session as DBSession

from database import get_db
from models import Session

router = APIRouter(prefix="/auth", tags=["auth"])

SESSION_DAYS = 7
COOKIE_NAME = "session"

def get_password() -> str:
    return os.environ.get("APP_PASSWORD", "zeltlager")


def _find_valid_session(token: str | None, db: DBSession) -> Session | None:
    if not token:
        return None
    session = db.get(Session, token)
    if not session:
        return None
    if session.expires_at < datetime.utcnow():
        db.delete(session)
        db.commit()
        return None
    return session


def _set_cookie(response: Response, token: str):
    response.set_cookie(
        COOKIE_NAME, token,
        httponly=True,
        max_age=SESSION_DAYS * 86400,
        samesite="lax",
    )


class LoginRequest(BaseModel):
    password: str


@router.post("/login")
def login(data: LoginRequest, response: Response, db: DBSession = Depends(get_db)):
    if data.password != get_password():
        raise HTTPException(status_code=401, detail="Falsches Passwort")

    token = secrets.token_hex(32)
    expires = datetime.utcnow() + timedelta(days=SESSION_DAYS)
    db.add(Session(token=token, expires_at=expires))
    db.commit()

    _set_cookie(response, token)
    return {"ok": True}


@router.post("/logout")
def logout(
    response: Response,
    session_token: str | None = Cookie(None, alias=COOKIE_NAME),
    db: DBSession = Depends(get_db),
):
    if session_token:
        session = db.get(Session, session_token)
        if session:
            db.delete(session)
            db.commit()
    response.delete_cookie(COOKIE_NAME)
    return {"ok": True}


@router.get("/check")
def check(
    response: Response,
    session_token: str | None = Cookie(None, alias=COOKIE_NAME),
    db: DBSession = Depends(get_db),
):
    session = _find_valid_session(session_token, db)
    if not session:
        raise HTTPException(status_code=401, detail="Nicht eingeloggt")
    # Sliding: Ablaufzeit verlängern
    session.expires_at = datetime.utcnow() + timedelta(days=SESSION_DAYS)
    db.commit()
    _set_cookie(response, session_token)
    return {"ok": True}
