from fastapi import APIRouter, Depends
from sqlalchemy import or_
from sqlalchemy.orm import Session
from database import get_db
from models import Item, Location
from schemas import ItemResponse, LocationResponse
from utils import get_breadcrumb, build_location_response

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/")
def search(q: str, db: Session = Depends(get_db)):
    if not q or len(q.strip()) < 1:
        return {"items": [], "locations": []}

    term = f"%{q.strip()}%"

    items = db.query(Item).filter(
        or_(
            Item.name.ilike(term),
            Item.description.ilike(term),
            Item.category.ilike(term),
            Item.tags.ilike(term),
            Item.notes.ilike(term),
        )
    ).order_by(Item.name).limit(50).all()

    locations = db.query(Location).filter(
        or_(
            Location.name.ilike(term),
            Location.description.ilike(term),
        )
    ).order_by(Location.name).limit(20).all()

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
            for i in items
        ],
        "locations": [build_location_response(l, db) for l in locations],
    }
