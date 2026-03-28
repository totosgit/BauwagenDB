from fastapi import APIRouter, Depends
from sqlalchemy import or_
from sqlalchemy.orm import Session
from rapidfuzz import fuzz
from database import get_db
from models import Item, Location
from utils import get_breadcrumb, build_location_response

router = APIRouter(prefix="/search", tags=["search"])

FUZZY_THRESHOLD = 75


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
def search(q: str, db: Session = Depends(get_db)):
    if not q or len(q.strip()) < 1:
        return {"items": [], "locations": []}

    query = q.strip()
    term = f"%{query}%"

    # Exakte Substring-Treffer (schnell, via DB)
    exact_items = db.query(Item).filter(
        or_(
            Item.name.ilike(term),
            Item.description.ilike(term),
            Item.category.ilike(term),
            Item.tags.ilike(term),
            Item.notes.ilike(term),
        )
    ).all()
    exact_item_ids = {i.id for i in exact_items}

    # Fuzzy-Matching über alle restlichen Items
    all_items = db.query(Item).filter(Item.id.notin_(exact_item_ids)).all()
    fuzzy_items = [
        i for i in all_items
        if _fuzzy_match(query, i.name, i.description, i.category, i.tags, i.notes)
    ]

    items = sorted(exact_items, key=lambda i: i.name) + sorted(fuzzy_items, key=lambda i: i.name)

    # Exakte Substring-Treffer Locations
    exact_locations = db.query(Location).filter(
        or_(
            Location.name.ilike(term),
            Location.description.ilike(term),
        )
    ).all()
    exact_location_ids = {l.id for l in exact_locations}

    # Fuzzy-Matching über alle restlichen Locations
    all_locations = db.query(Location).filter(Location.id.notin_(exact_location_ids)).all()
    fuzzy_locations = [
        l for l in all_locations
        if _fuzzy_match(query, l.name, l.description)
    ]

    locations = sorted(exact_locations, key=lambda l: l.name) + sorted(fuzzy_locations, key=lambda l: l.name)

    return {
        "items": [
            {
                "id": i.id,
                "name": i.name,
                "category": i.category,
                "quantity": i.quantity,
                "unit": i.unit,
                "image_path": i.image_path,
                "breadcrumb_lager": get_breadcrumb(db, i.location_lager_id),
                "breadcrumb_jahr": get_breadcrumb(db, i.location_jahr_id),
                "location_lager_id": i.location_lager_id,
                "location_jahr_id": i.location_jahr_id,
                "tags": i.tags,
                "aufgebaut": i.aufgebaut,
            }
            for i in items[:50]
        ],
        "locations": [build_location_response(l, db) for l in locations[:20]],
    }
