"""Suche über Gegenstände und Lagerorte.

Lagerorte sind wieder dabei, aber als eigener Abschnitt: ganze Kisten
werden ausgeliehen, also muss man sie auch finden koennen. Getrennt
gehalten, damit die Trefferliste nicht vermischt.
"""
from fastapi import APIRouter, Depends
from rapidfuzz import fuzz
from sqlalchemy import or_
from sqlalchemy.orm import Session

from auth import current_user
from database import get_db
from models import Item, Location, User
from utils import alle_breadcrumbs

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


@router.get("/")
def search(
    q: str,
    mode: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(current_user),
):
    if not q or not q.strip():
        return {"items": [], "orte": []}

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

    # Lagerorte: exakt und unscharf, gleiche Regeln wie bei Gegenstaenden
    ort_basis = db.query(Location)
    if mode:
        ort_basis = ort_basis.filter(Location.storage_mode.in_([mode, "both"]))
    orte_exakt = ort_basis.filter(
        or_(Location.name.ilike(term), Location.description.ilike(term))
    ).all()
    ort_ids = {o.id for o in orte_exakt}
    orte_rest = [o for o in ort_basis.all() if o.id not in ort_ids]
    orte_fuzzy = [o for o in orte_rest if _fuzzy_match(query, o.name, o.description)]
    orte = (sorted(orte_exakt, key=lambda o: o.name)
            + sorted(orte_fuzzy, key=lambda o: o.name))[:MAX_TREFFER]

    pfade = alle_breadcrumbs(db, "lager")
    pfade_jahr = alle_breadcrumbs(db, "jahr")
    zaehler = {}
    if orte:
        from sqlalchemy import func
        for oid, anzahl in (
            db.query(Item.location_lager_id, func.count(Item.id))
            .filter(Item.location_lager_id.in_([o.id for o in orte]))
            .group_by(Item.location_lager_id).all()
        ):
            zaehler[oid] = anzahl

    return {
        "orte": [
            {
                "id": o.id,
                "name": o.name,
                "type": o.type,
                "breadcrumb": (pfade_jahr if mode == "jahr" else pfade).get(o.id, ""),
                "item_count": zaehler.get(o.id, 0),
            }
            for o in orte
        ],
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
                "breadcrumb_jahr": pfade_jahr.get(i.location_jahr_id, ""),
                "location_lager_id": i.location_lager_id,
                "location_jahr_id": i.location_jahr_id,
                "tags": i.tags,
                "aufgebaut": i.aufgebaut,
                "aufgebaut_notiz": i.aufgebaut_notiz,
            }
            for i in treffer
        ]
    }
