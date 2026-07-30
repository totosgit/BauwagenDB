"""Öffentliche Strichliste.

Jeder sieht die Striche aller anderen, setzt und löscht aber ausschließlich
seine eigenen. Nur das Zurücksetzen bei der Abrechnung ist Admins vorbehalten.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from auth import current_admin, current_user
from database import get_db
from models import Drink, Tally, User
from schemas import TallyCreate, TallyResponse, TallySummary, TallySummaryEntry

router = APIRouter(prefix="/tally", tags=["tally"])


def _summaries_for(db: Session, users: list[User], me: User) -> list[TallySummary]:
    """Baut die Übersicht für mehrere Benutzer mit zwei Queries statt N+1."""
    if not users:
        return []

    user_ids = [u.id for u in users]
    rows = (
        db.query(Tally.user_id, Tally.drink_id, func.sum(Tally.count).label("total"))
        .filter(Tally.user_id.in_(user_ids))
        .group_by(Tally.user_id, Tally.drink_id)
        .all()
    )
    drinks = {d.id: d for d in db.query(Drink).all()}

    per_user: dict[str, list[TallySummaryEntry]] = {}
    for user_id, drink_id, total in rows:
        drink = drinks.get(drink_id)
        per_user.setdefault(str(user_id), []).append(
            TallySummaryEntry(
                drink_id=drink_id,
                drink_name=drink.name if drink else "?",
                drink_emoji=drink.emoji if drink else None,
                total=total,
            )
        )

    result = []
    for user in users:
        entries = sorted(per_user.get(str(user.id), []), key=lambda e: e.drink_name)
        result.append(
            TallySummary(
                user_id=user.id,
                username=user.username,
                display_name=user.display_name,
                entries=entries,
                grand_total=sum(e.total for e in entries),
                is_self=user.id == me.id,
            )
        )
    return result


@router.get("/", response_model=list[TallySummary])
def list_all(db: Session = Depends(get_db), me: User = Depends(current_user)):
    """Die öffentliche Liste: alle freigegebenen Benutzer, eigener zuerst."""
    users = (
        db.query(User)
        .filter(User.is_active == True)  # noqa: E712
        .order_by(User.display_name)
        .all()
    )
    summaries = _summaries_for(db, users, me)
    summaries.sort(key=lambda s: (not s.is_self, s.display_name.lower()))
    return summaries


@router.get("/me", response_model=TallySummary)
def my_summary(db: Session = Depends(get_db), me: User = Depends(current_user)):
    return _summaries_for(db, [me], me)[0]


@router.post("/", response_model=TallyResponse, status_code=201)
def add_tally(
    data: TallyCreate,
    db: Session = Depends(get_db),
    me: User = Depends(current_user),
):
    """Setzt einen Strich -- immer für den angemeldeten Benutzer selbst."""
    if data.count < 1:
        raise HTTPException(status_code=400, detail="Anzahl muss mindestens 1 sein")
    if not db.get(Drink, data.drink_id):
        raise HTTPException(status_code=404, detail="Getränk nicht gefunden")

    tally = Tally(user_id=me.id, drink_id=data.drink_id, count=data.count)
    db.add(tally)
    db.commit()
    db.refresh(tally)
    return tally


@router.delete("/last/{drink_id}", status_code=204)
def remove_last(
    drink_id: int,
    db: Session = Depends(get_db),
    me: User = Depends(current_user),
):
    """Nimmt den zuletzt gesetzten eigenen Strich zurück (Vertippt-Korrektur)."""
    tally = (
        db.query(Tally)
        .filter(Tally.user_id == me.id, Tally.drink_id == drink_id)
        .order_by(Tally.created_at.desc(), Tally.id.desc())
        .first()
    )
    if tally is None:
        raise HTTPException(status_code=404, detail="Kein Strich zum Zurücknehmen")

    if tally.count > 1:
        tally.count -= 1
    else:
        db.delete(tally)
    db.commit()


@router.delete("/reset/{user_id}", status_code=204)
def reset_tallies(
    user_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(current_admin),
):
    """Abrechnung: alle Striche eines Benutzers löschen. Nur für Admins."""
    if not db.get(User, user_id):
        raise HTTPException(status_code=404, detail="Benutzer nicht gefunden")
    db.query(Tally).filter(Tally.user_id == user_id).delete()
    db.commit()


@router.delete("/", status_code=200)
def reset_all_tallies(db: Session = Depends(get_db), _: User = Depends(current_admin)):
    """Abrechnung für alle auf einmal: die ganze Strichliste auf null.

    Gedacht für den Ablauf am Ende des Lagers -- erst als PDF sichern, dann
    hier leeren. Gibt zurück, wie viele Striche weg sind, damit die Meldung
    im Frontend nicht raten muss.
    """
    anzahl = db.query(func.coalesce(func.sum(Tally.count), 0)).scalar() or 0
    zeilen = db.query(Tally).delete()
    db.commit()
    return {"striche": int(anzahl), "zeilen": int(zeilen)}
