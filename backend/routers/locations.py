"""Lagerorte.

Lesen darf jeder Angemeldete -- der Zuordnungs-Assistent im
Gegenstandsformular braucht die Liste. Anlegen, umbauen und loeschen ist
Verwaltungsarbeit und deshalb Admins vorbehalten.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from auth import current_admin, current_user
from database import get_db
from models import Location, Item, User
from schemas import LocationCreate, LocationUpdate, LocationResponse, LocationTree
from utils import build_location_response, build_location_tree

router = APIRouter(prefix="/locations", tags=["locations"])

# Erlaubte Kind-Typen pro Eltern-Typ (None = Root-Ebene)
VALID_CHILDREN: dict[str | None, list[str]] = {
    None:        ["bauwagen", "schopf", "sonstiges"],
    "bauwagen":  ["regal", "schrank", "kiste", "wand"],
    "schopf":    ["regal", "schrank", "kiste", "wand"],
    "sonstiges": ["regal", "schrank", "kiste", "wand", "sonstiges"],
    "regal":     ["fach"],
    "fach":      ["boden"],
    "schrank":   ["boden"],
    "boden":     ["kiste"],
    "kiste":     [],
    "wand":      [],
}


def validate_type(parent: Location | None, child_type: str):
    parent_type = parent.type if parent else None
    allowed = VALID_CHILDREN.get(parent_type, [])
    if child_type not in allowed:
        parent_label = f"'{parent.name}' ({parent_type})" if parent else "der Root-Ebene"
        raise HTTPException(
            status_code=400,
            detail=f"Typ '{child_type}' ist unter {parent_label} nicht erlaubt. Erlaubt: {allowed or 'keine Kinder moeglich'}",
        )


def sorted_siblings(db: Session, parent_id: int | None) -> list[Location]:
    return (
        db.query(Location)
        .filter(Location.parent_id == parent_id)
        .order_by(Location.sort_order, Location.id)
        .all()
    )


def normalize_and_commit(db: Session, siblings: list[Location]):
    """Weist allen Geschwistern saubere sort_order-Werte zu (0, 10, 20, ...)."""
    for i, s in enumerate(siblings):
        s.sort_order = i * 10
    db.commit()


@router.get("/types", response_model=dict)
def get_valid_types(_: User = Depends(current_user)):
    return VALID_CHILDREN


@router.get("/", response_model=list[LocationResponse])
def list_locations(mode: str | None = None, db: Session = Depends(get_db), _: User = Depends(current_user)):
    q = db.query(Location).order_by(Location.sort_order, Location.id)
    if mode:
        q = q.filter(Location.storage_mode.in_([mode, "both"]))
    return [build_location_response(l, db) for l in q.all()]


@router.get("/tree", response_model=list[LocationTree])
def get_tree(mode: str | None = None, db: Session = Depends(get_db), _: User = Depends(current_user)):
    q = (
        db.query(Location)
        .filter(Location.parent_id == None)
        .order_by(Location.sort_order, Location.id)
    )
    if mode:
        q = q.filter(Location.storage_mode.in_([mode, "both"]))
    return [build_location_tree(r, db) for r in q.all()]


@router.get("/{location_id}", response_model=LocationTree)
def get_location(location_id: int, db: Session = Depends(get_db), _: User = Depends(current_user)):
    loc = db.get(Location, location_id)
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")
    return build_location_tree(loc, db)


@router.post("/", response_model=LocationResponse, status_code=201)
def create_location(data: LocationCreate, db: Session = Depends(get_db), _: User = Depends(current_admin)):
    parent = None
    if data.parent_id:
        parent = db.get(Location, data.parent_id)
        if not parent:
            raise HTTPException(status_code=404, detail="Parent location not found")
    validate_type(parent, data.type)

    siblings = sorted_siblings(db, data.parent_id)
    next_order = (siblings[-1].sort_order + 10) if siblings else 0

    loc = Location(**data.model_dump())
    loc.sort_order = next_order
    db.add(loc)
    db.commit()
    db.refresh(loc)
    return build_location_response(loc, db)


@router.put("/{location_id}", response_model=LocationResponse)
def update_location(location_id: int, data: LocationUpdate, db: Session = Depends(get_db), _: User = Depends(current_admin)):
    loc = db.get(Location, location_id)
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")
    new_type = data.type if data.type is not None else loc.type
    new_parent_id = data.parent_id if "parent_id" in data.model_fields_set else loc.parent_id
    parent = db.get(Location, new_parent_id) if new_parent_id else None
    validate_type(parent, new_type)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(loc, field, value)
    db.commit()
    db.refresh(loc)
    return build_location_response(loc, db)


@router.post("/reorder", status_code=204)
def reorder_locations(ordered_ids: list[int], db: Session = Depends(get_db), _: User = Depends(current_admin)):
    """Setzt die sort_order aller Geschwister auf Basis der übergebenen ID-Reihenfolge."""
    for i, loc_id in enumerate(ordered_ids):
        loc = db.get(Location, loc_id)
        if loc:
            loc.sort_order = i * 10
    db.commit()


@router.patch("/{location_id}/move", response_model=LocationResponse)
def move_location(location_id: int, direction: str, db: Session = Depends(get_db), _: User = Depends(current_admin)):
    """Verschiebt einen Lagerort in der Reihenfolge seiner Geschwister nach oben oder unten."""
    loc = db.get(Location, location_id)
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")

    siblings = sorted_siblings(db, loc.parent_id)
    idx = next((i for i, s in enumerate(siblings) if s.id == location_id), None)
    if idx is None:
        return build_location_response(loc, db)

    target_idx = idx - 1 if direction == "up" else idx + 1
    if target_idx < 0 or target_idx >= len(siblings):
        return build_location_response(loc, db)

    # Normalisieren, dann tauschen
    normalize_and_commit(db, siblings)
    siblings[idx].sort_order, siblings[target_idx].sort_order = (
        siblings[target_idx].sort_order,
        siblings[idx].sort_order,
    )
    db.commit()
    db.refresh(loc)
    return build_location_response(loc, db)


@router.delete("/{location_id}", status_code=204)
def delete_location(location_id: int, db: Session = Depends(get_db), _: User = Depends(current_admin)):
    loc = db.get(Location, location_id)
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")
    item_count = db.query(Item).filter(
        or_(Item.location_lager_id == location_id, Item.location_jahr_id == location_id)
    ).count()
    if item_count:
        raise HTTPException(status_code=400, detail="Location still has items. Move or delete them first.")
    db.delete(loc)
    db.commit()
