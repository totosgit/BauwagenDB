"""Profile, Benutzerliste und Admin-Freigaben.

Synchron gehalten wie der Rest der Router. Passwoerter werden mit demselben
Helper gehasht, den auch der async UserManager benutzt.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import MIN_PASSWORD_LENGTH, password_helper
from auth import current_admin, current_user
from database import get_db
from models import AccessToken, User
from schemas import PasswordReset, UserAdminUpdate, UserMe, UserPublic, UserUpdateSelf

router = APIRouter(prefix="/users", tags=["users"])


def _get_user_or_404(db: Session, user_id: str) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Benutzer nicht gefunden")
    return user


@router.get("/", response_model=list[UserPublic])
def list_users(db: Session = Depends(get_db), _: User = Depends(current_user)):
    """Alle freigegebenen Benutzer -- Grundlage fuer Profile und Strichliste."""
    return (
        db.query(User)
        .filter(User.is_active == True)  # noqa: E712
        .order_by(User.display_name)
        .all()
    )


@router.get("/pending", response_model=list[UserPublic])
def list_pending(db: Session = Depends(get_db), _: User = Depends(current_admin)):
    """Registrierungen, die noch auf Freigabe warten."""
    return (
        db.query(User)
        .filter(User.is_active == False)  # noqa: E712
        .order_by(User.created_at)
        .all()
    )


@router.patch("/me", response_model=UserMe)
def update_me(
    data: UserUpdateSelf,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    if data.display_name is not None:
        user.display_name = data.display_name

    if data.email is not None:
        clash = db.query(User).filter(User.email == data.email, User.id != user.id).first()
        if clash:
            raise HTTPException(status_code=409, detail="Diese E-Mail wird bereits verwendet")
        user.email = data.email

    if data.password is not None:
        if not data.current_password:
            raise HTTPException(status_code=400, detail="Bitte das aktuelle Passwort angeben")
        valid, _ = password_helper.verify_and_update(data.current_password, user.hashed_password)
        if not valid:
            raise HTTPException(status_code=403, detail="Das aktuelle Passwort ist falsch")
        if len(data.password) < MIN_PASSWORD_LENGTH:
            raise HTTPException(
                status_code=400,
                detail=f"Das Passwort muss mindestens {MIN_PASSWORD_LENGTH} Zeichen lang sein.",
            )
        user.hashed_password = password_helper.hash(data.password)
        # Andere Geraete abmelden, das eigene Cookie bleibt gueltig.
        db.query(AccessToken).filter(AccessToken.user_id == user.id).delete()

    db.commit()
    db.refresh(user)
    return user


@router.get("/{user_id}", response_model=UserPublic)
def get_user(user_id: str, db: Session = Depends(get_db), _: User = Depends(current_user)):
    return _get_user_or_404(db, user_id)


@router.patch("/{user_id}", response_model=UserPublic)
def admin_update_user(
    user_id: str,
    data: UserAdminUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(current_admin),
):
    """Freigeben, sperren oder zum Admin machen."""
    user = _get_user_or_404(db, user_id)

    if data.is_superuser is not None and user.id == admin.id and not data.is_superuser:
        raise HTTPException(status_code=400, detail="Du kannst dir nicht selbst die Adminrechte entziehen")
    if data.is_active is not None and user.id == admin.id and not data.is_active:
        raise HTTPException(status_code=400, detail="Du kannst dich nicht selbst sperren")

    if data.display_name is not None:
        user.display_name = data.display_name
    if data.is_superuser is not None:
        user.is_superuser = data.is_superuser
    if data.is_active is not None:
        user.is_active = data.is_active
        if not data.is_active:
            # Gesperrte Benutzer sofort abmelden
            db.query(AccessToken).filter(AccessToken.user_id == user.id).delete()

    db.commit()
    db.refresh(user)
    return user


@router.post("/{user_id}/password", status_code=204)
def admin_reset_password(
    user_id: str,
    data: PasswordReset,
    db: Session = Depends(get_db),
    _: User = Depends(current_admin),
):
    """Passwort-Reset laeuft ueber einen Admin -- wir haben keinen Mailversand."""
    user = _get_user_or_404(db, user_id)
    user.hashed_password = password_helper.hash(data.password)
    db.query(AccessToken).filter(AccessToken.user_id == user.id).delete()
    db.commit()


@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(current_admin),
):
    user = _get_user_or_404(db, user_id)
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Du kannst dich nicht selbst löschen")
    db.delete(user)
    db.commit()
