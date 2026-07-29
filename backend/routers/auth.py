"""Login, Logout und Registrierung.

Der Login-Endpunkt ist bewusst selbst geschrieben statt fastapi-users'
Standard-Router zu nutzen: der antwortet auf "falsches Passwort" und "noch
nicht freigegeben" identisch. Im Zeltlager-Alltag ist der Unterschied aber
genau die Information, die jemand braucht.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi_users import exceptions

from auth import (
    COOKIE_NAME,
    UserManager,
    auth_backend,
    current_user,
    get_database_strategy,
    get_user_manager,
)
from models import User
from schemas import LoginRequest, UserMe, UserRegister

router = APIRouter(prefix="/auth", tags=["auth"])


class _Credentials:
    """Minimal-Ersatz fuer OAuth2PasswordRequestForm -- wir nehmen JSON."""

    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password


@router.post("/login")
async def login(
    data: LoginRequest,
    user_manager: UserManager = Depends(get_user_manager),
    strategy=Depends(get_database_strategy),
):
    user = await user_manager.authenticate(_Credentials(data.username, data.password))

    if user is None:
        raise HTTPException(status_code=401, detail="Benutzername oder Passwort ist falsch")
    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Dein Konto wurde noch nicht freigegeben. Ein Admin muss das bestätigen.",
        )

    return await auth_backend.login(strategy, user)


@router.post("/logout")
async def logout(
    request: Request,
    strategy=Depends(get_database_strategy),
):
    token = request.cookies.get(COOKIE_NAME)
    user = getattr(request.state, "user", None)
    if token and user is not None:
        return await auth_backend.logout(strategy, user, token)
    response = Response(status_code=204)
    response.delete_cookie(COOKIE_NAME)
    return response


@router.post("/register", status_code=201)
async def register(
    data: UserRegister,
    user_manager: UserManager = Depends(get_user_manager),
):
    try:
        await user_manager.register(
            username=data.username,
            display_name=data.display_name,
            password=data.password,
            email=data.email,
        )
    except exceptions.UserAlreadyExists:
        raise HTTPException(status_code=409, detail="Benutzername oder E-Mail ist bereits vergeben")
    except exceptions.InvalidPasswordException as e:
        raise HTTPException(status_code=400, detail=e.reason)

    return {
        "ok": True,
        "detail": "Konto angelegt. Ein Admin muss es noch freigeben, danach kannst du dich anmelden.",
    }


@router.get("/me", response_model=UserMe)
def me(user: User = Depends(current_user)):
    return user
