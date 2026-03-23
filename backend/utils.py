from sqlalchemy import or_
from sqlalchemy.orm import Session
from models import Location, Item


def get_breadcrumb(db: Session, location_id: int | None) -> str:
    if location_id is None:
        return ""
    parts = []
    current_id = location_id
    seen = set()
    while current_id and current_id not in seen:
        seen.add(current_id)
        loc = db.get(Location, current_id)
        if loc is None:
            break
        parts.append(loc.name)
        current_id = loc.parent_id
    parts.reverse()
    return " › ".join(parts)


def build_location_response(loc: Location, db: Session) -> dict:
    item_count = db.query(Item).filter(
        or_(Item.location_lager_id == loc.id, Item.location_jahr_id == loc.id)
    ).count()
    return {
        "id": loc.id,
        "name": loc.name,
        "description": loc.description,
        "type": loc.type,
        "storage_mode": loc.storage_mode,
        "coordinate_x": loc.coordinate_x,
        "coordinate_y": loc.coordinate_y,
        "coordinate_z": loc.coordinate_z,
        "parent_id": loc.parent_id,
        "created_at": loc.created_at,
        "item_count": item_count,
        "breadcrumb": get_breadcrumb(db, loc.id),
    }


def build_location_tree(loc: Location, db: Session) -> dict:
    data = build_location_response(loc, db)
    data["children"] = [build_location_tree(child, db) for child in loc.children]
    return data
