"""Anwendungsweite Einstellungen.

Aktuell nur der Lagerzeitraum: daraus leitet die App ab, ob sie
standardmaessig den Lager- oder den Jahresbetrieb zeigt. Lesen darf jeder
Angemeldete, aendern nur Admins.
"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import current_admin, current_user
from database import get_db
from models import Einstellung, User
from schemas import LagerZeitraum, LagerZeitraumUpdate

router = APIRouter(prefix="/einstellungen", tags=["einstellungen"])

START = "lager_start"
ENDE = "lager_ende"


def _lies(db: Session, schluessel: str) -> str | None:
    eintrag = db.get(Einstellung, schluessel)
    return eintrag.wert if eintrag else None


def _schreib(db: Session, schluessel: str, wert: str | None) -> None:
    eintrag = db.get(Einstellung, schluessel)
    if eintrag is None:
        eintrag = Einstellung(schluessel=schluessel)
        db.add(eintrag)
    eintrag.wert = wert


def _als_datum(text: str | None) -> date | None:
    if not text:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def _zeitraum(db: Session) -> dict:
    start = _als_datum(_lies(db, START))
    ende = _als_datum(_lies(db, ENDE))
    heute = date.today()

    # Ohne Zeitraum bleibt es beim Jahresbetrieb -- das ist die meiste Zeit
    # der richtige Zustand und aendert nichts an dem, was Leute gewohnt sind.
    laeuft = bool(start and ende and start <= heute <= ende)
    return {
        "start": start,
        "ende": ende,
        "laeuft_gerade": laeuft,
        "empfohlener_modus": "lager" if laeuft else "jahr",
        "heute": heute,
    }


@router.get("/lager-zeitraum", response_model=LagerZeitraum)
def lager_zeitraum(db: Session = Depends(get_db), _: User = Depends(current_user)):
    return _zeitraum(db)


@router.put("/lager-zeitraum", response_model=LagerZeitraum)
def setze_lager_zeitraum(
    data: LagerZeitraumUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(current_admin),
):
    if data.start and data.ende and data.ende < data.start:
        raise HTTPException(status_code=400, detail="Das Ende liegt vor dem Beginn")

    _schreib(db, START, data.start.isoformat() if data.start else None)
    _schreib(db, ENDE, data.ende.isoformat() if data.ende else None)
    db.commit()
    return _zeitraum(db)
