"""Suche über Gegenstände.

Lagerorte werden bewusst nicht durchsucht -- man sucht Dinge, nicht Orte.
Durch die Struktur blättert man in der Orte-Ansicht.
"""
from fastapi import APIRouter, Depends
from rapidfuzz import fuzz
from sqlalchemy import or_
from sqlalchemy.orm import Session

from auth import current_user
from database import get_db
from models import Item, Location, User

router = APIRouter(prefix="/search", tags=["search"])

FUZZY_THRESHOLD = 75
MAX_TREFFER = 50


def _fuzzy_match(query: str, *fields: str) -> bool:
    q = query.lower()
    for field in fields:
        if not field:
            continue
        # Einzelne Wörter im Feld gegen Query prüfen
        for word in field.lower().split():
            if fuzz.ratio(q, word) >= FUZZY_THRESHOLD:
                return True
        # Auch den ganzen Feldinhalt als Substring prüfen
        if fuzz.partial_ratio(q, field.lower()) >= FUZZY_THRESHOLD:
            return True
    return False


def _breadcrumbs(db: Session) -> dict[int, str]:
    """Alle Pfade in einer Abfrage statt einer Kette pro Gegenstand.

    Vorher lief für jeden Treffer eine eigene Abfragekette bis zur Wurzel --
    bei 50 Treffern schnell hunderte Abfragen auf dem Raspberry Pi.
    """
    orte = {
        o.id: (o.name, o.parent_id)
        for o in db.query(Location.id, Location.name, Location.parent_id).all()
    }

    fertig: dict[int, str] = {}

    def pfad(oid: int | None) -> str:
        if oid is None or oid not in orte:
            return ""
        if oid in fertig:
            return fertig[oid]
        name, parent = orte[oid]
        # Zyklenschutz: erst belegen, dann auflösen
        fertig[oid] = name
        oben = pfad(parent)
        fertig[oid] = f"{oben} › {name}" if oben else name
        return fertig[oid]

    for oid in orte:
        pfad(oid)
    return fertig


@router.get("/")
def search(
    q: str,
    mode: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(current_user),
):
    if not q or not q.strip():
        return {"items": []}

    query = q.strip()
    term = f"%{query}%"

    basis = db.query(Item)
    if mode:
        basis = basis.filter(Item.storage_mode.in_([mode, "both"]))

    # Exakte Substring-Treffer zuerst (schnell, über die Datenbank)
    exact = basis.filter(
        or_(
            Item.name.ilike(term),
            Item.description.ilike(term),
            Item.category.ilike(term),
            Item.tags.ilike(term),
            Item.notes.ilike(term),
        )
    ).all()
    exact_ids = {i.id for i in exact}

    # Danach unscharf über den Rest (Tippfehler, Wortformen)
    rest = basis.filter(Item.id.notin_(exact_ids)).all() if exact_ids else basis.all()
    fuzzy = [
        i for i in rest
        if i.id not in exact_ids
        and _fuzzy_match(query, i.name, i.description, i.category, i.tags, i.notes)
    ]

    treffer = sorted(exact, key=lambda i: i.name) + sorted(fuzzy, key=lambda i: i.name)
    treffer = treffer[:MAX_TREFFER]

    pfade = _breadcrumbs(db)
    return {
        "items": [
            {
                "id": i.id,
                "name": i.name,
                "category": i.category,
                "quantity": i.quantity,
                "unit": i.unit,
                "image_path": i.image_path,
                "storage_mode": i.storage_mode,
                "breadcrumb_lager": pfade.get(i.location_lager_id, ""),
                "breadcrumb_jahr": pfade.get(i.location_jahr_id, ""),
                "location_lager_id": i.location_lager_id,
                "location_jahr_id": i.location_jahr_id,
                "tags": i.tags,
                "aufgebaut": i.aufgebaut,
            }
            for i in treffer
        ]
    }
