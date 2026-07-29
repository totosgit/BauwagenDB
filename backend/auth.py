"""Authentifizierung auf Basis von fastapi-users.

Bewusste Abweichung vom Standard: Angemeldet wird sich mit einem
Benutzernamen, nicht mit einer E-Mail-Adresse. Im Zeltlager gibt es keinen
Mailserver, ein Passwort-Reset laeuft ueber einen Admin.

Alles Sicherheitskritische (Passwort-Hashing, Token-Erzeugung, Cookie-
Handling) kommt aus fastapi-users. Selbst geschrieben ist nur die Logik
drumherum: Login per Benutzername, Registrierung und Freigabe.
"""
import os
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin, exceptions
from fastapi_users.authentication import AuthenticationBackend, CookieTransport
from fastapi_users.authentication.strategy.db import AccessTokenDatabase, DatabaseStrategy
from fastapi_users.password import PasswordHelper
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from fastapi_users_db_sqlalchemy.access_token import SQLAlchemyAccessTokenDatabase
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session as SyncSession

from database import get_async_db, get_db
from models import AccessToken, User

COOKIE_NAME = "bauwagen_session"
SESSION_DAYS = 7
SESSION_SECONDS = SESSION_DAYS * 86400
# Ablaufdatum nur verlaengern wenn das Token aelter als ein Tag ist -- sonst
# schreibt jeder einzelne Request auf die SD-Karte des Raspberry Pi.
SESSION_REFRESH_AFTER = timedelta(days=1)

# Nur fuer Passwort-Reset-Tokens noetig, die wir aktuell nicht nutzen.
SECRET = os.environ.get("SECRET_KEY") or uuid.uuid4().hex

# Ueber HTTPS ausgeliefert -> Secure-Cookie. Fuer lokale Entwicklung abschaltbar.
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "true").lower() not in ("0", "false", "no")

MIN_PASSWORD_LENGTH = 8

# Ein gemeinsamer Helper fuer async (UserManager) und die synchronen Router,
# damit beide Seiten garantiert dasselbe Hash-Verfahren benutzen.
password_helper = PasswordHelper()


class UserDatabase(SQLAlchemyUserDatabase):
    """Ergaenzt die Suche nach Benutzername."""

    async def get_by_username(self, username: str) -> User | None:
        statement = select(self.user_table).where(
            func.lower(self.user_table.username) == func.lower(username)
        )
        return await self._get_user(statement)


async def get_user_db(session: AsyncSession = Depends(get_async_db)):
    yield UserDatabase(session, User)


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def validate_password(self, password: str, user=None) -> None:
        if len(password) < MIN_PASSWORD_LENGTH:
            raise exceptions.InvalidPasswordException(
                reason=f"Das Passwort muss mindestens {MIN_PASSWORD_LENGTH} Zeichen lang sein."
            )

    async def authenticate(self, credentials: OAuth2PasswordRequestForm) -> User | None:
        """Wie das Original, nur ueber username statt email."""
        user = await self.user_db.get_by_username(credentials.username)
        if user is None:
            # Trotzdem hashen, damit ein nicht existierender Benutzer nicht
            # an der kuerzeren Antwortzeit erkennbar ist.
            self.password_helper.hash(credentials.password)
            return None

        verified, updated_hash = self.password_helper.verify_and_update(
            credentials.password, user.hashed_password
        )
        if not verified:
            return None
        if updated_hash is not None:
            await self.user_db.update(user, {"hashed_password": updated_hash})
        return user

    async def register(
        self,
        username: str,
        display_name: str,
        password: str,
        email: str | None = None,
        is_active: bool = False,
        is_superuser: bool = False,
    ) -> User:
        """Legt ein Konto an. Standardmaessig inaktiv -- ein Admin gibt es frei."""
        await self.validate_password(password)

        if await self.user_db.get_by_username(username) is not None:
            raise exceptions.UserAlreadyExists()
        if email and await self.user_db.get_by_email(email) is not None:
            raise exceptions.UserAlreadyExists()

        return await self.user_db.create({
            "username": username,
            "display_name": display_name,
            "email": email,
            "hashed_password": self.password_helper.hash(password),
            "is_active": is_active,
            "is_superuser": is_superuser,
            "is_verified": False,
        })


async def get_user_manager(user_db: UserDatabase = Depends(get_user_db)):
    yield UserManager(user_db, password_helper)


cookie_transport = CookieTransport(
    cookie_name=COOKIE_NAME,
    cookie_max_age=SESSION_SECONDS,
    cookie_secure=COOKIE_SECURE,
    cookie_httponly=True,
    cookie_samesite="lax",
)


async def get_access_token_db(session: AsyncSession = Depends(get_async_db)):
    yield SQLAlchemyAccessTokenDatabase(session, AccessToken)


def get_database_strategy(
    access_token_db: AccessTokenDatabase[AccessToken] = Depends(get_access_token_db),
) -> DatabaseStrategy:
    return DatabaseStrategy(access_token_db, lifetime_seconds=SESSION_SECONDS)


auth_backend = AuthenticationBackend(
    name="cookie",
    transport=cookie_transport,
    get_strategy=get_database_strategy,
)

fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])


# --- Synchrone Variante fuer Middleware und die bestehenden Sync-Router ---

def resolve_session(db: SyncSession, token: str | None) -> User | None:
    """Prueft das Session-Cookie gegen die Datenbank.

    Laeuft synchron, damit Middleware und die bestehenden Router dieselbe
    Pruefung nutzen koennen ohne async zu werden.
    """
    if not token:
        return None

    access_token = db.get(AccessToken, token)
    if access_token is None:
        return None

    created = access_token.created_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    if created + timedelta(seconds=SESSION_SECONDS) < now:
        db.delete(access_token)
        db.commit()
        return None

    user_id = access_token.user_id

    # Sliding expiry, aber sparsam (siehe SESSION_REFRESH_AFTER).
    # Wichtig: das commit() muss VOR dem Laden des Benutzers passieren --
    # sonst markiert es das User-Objekt als veraltet und der Zugriff darauf
    # scheitert, sobald die Session geschlossen ist.
    if now - created > SESSION_REFRESH_AFTER:
        access_token.created_at = now
        db.commit()

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        return None

    return user


def current_user(request: Request, db: SyncSession = Depends(get_db)) -> User:
    """Der von der Middleware geprüfte Benutzer, an die Session des Requests
    gebunden.

    Die Middleware benutzt eine eigene, sofort wieder geschlossene Session.
    Deren Objekt ist danach losgeloest -- Aenderungen daran wuerden von einem
    db.commit() im Router nicht gespeichert. Deshalb hier einmal frisch laden.
    """
    cached = getattr(request.state, "user", None)
    if cached is None:
        raise HTTPException(status_code=401, detail="Nicht angemeldet")

    user = db.get(User, cached.id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Nicht angemeldet")
    return user


def current_admin(user: User = Depends(current_user)) -> User:
    if not user.is_superuser:
        raise HTTPException(status_code=403, detail="Nur für Admins")
    return user
