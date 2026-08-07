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


def ist_nachfahre(db: Session, kandidat_id: int, moeglicher_vorfahre_id: int,
                  modus: str = "lager") -> bool:
    """Liegt kandidat_id unterhalb von moeglicher_vorfahre_id?

    Wird gebraucht, damit ein Ort nicht in sich selbst verschoben werden
    kann. Ohne diese Pruefung entstuende ein Kreis, und der Baumaufbau
    liefe endlos. Gilt fuer beide Baeume -- unter dem Jahr kann ein Ort
    ueber parent_jahr_id woanders haengen.
    """
    gesehen = set()
    aktuell = kandidat_id
    while aktuell is not None and aktuell not in gesehen:
        if aktuell == moeglicher_vorfahre_id:
            return True
        gesehen.add(aktuell)
        ort = db.get(Location, aktuell)
        if ort is None:
            return False
        if modus == "jahr" and ort.parent_jahr_id:
            aktuell = ort.parent_jahr_id
        else:
            aktuell = ort.parent_id
    return False


def pruefe_verschiebung(db: Session, loc: Location, neuer_parent_id: int | None,
                        modus: str = "lager") -> Location | None:
    """Gemeinsame Pruefung fuer Umhaengen. Gibt den neuen Elternort zurueck."""
    if neuer_parent_id is None:
        return None
    if neuer_parent_id == loc.id:
        raise HTTPException(status_code=400, detail="Ein Ort kann nicht in sich selbst liegen")
    ziel = db.get(Location, neuer_parent_id)
    if ziel is None:
        raise HTTPException(status_code=404, detail="Zielort nicht gefunden")
    if ist_nachfahre(db, neuer_parent_id, loc.id, modus):
        raise HTTPException(
            status_code=400,
            detail=f"'{ziel.name}' liegt innerhalb von '{loc.name}' -- das ergaebe einen Kreis",
        )
    return ziel


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
    if new_parent_id != loc.parent_id:
        parent = pruefe_verschiebung(db, loc, new_parent_id)
    else:
        parent = db.get(Location, new_parent_id) if new_parent_id else None
    validate_type(parent, new_type)

    # Der Jahr-Elternteil braucht dieselbe Pruefung, sonst laesst sich ueber
    # ihn ein Kreis bauen.
    if "parent_jahr_id" in data.model_fields_set and data.parent_jahr_id != loc.parent_jahr_id:
        if data.parent_jahr_id is not None:
            ziel_jahr = pruefe_verschiebung(db, loc, data.parent_jahr_id, "jahr")
            validate_type(ziel_jahr, new_type)
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


@router.get("/{location_id}/verschiebe-ziele", response_model=list[LocationResponse])
def verschiebe_ziele(
    location_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(current_user),
):
    """Wohin darf dieser Ort verschoben werden?

    Erlaubt sind alle Orte, unter denen der Typ zulaessig ist und die nicht
    im Ort selbst liegen. Zusaetzlich die Root-Ebene, falls der Typ dort
    stehen darf -- als eigener Eintrag mit id 0.
    """
    loc = db.get(Location, location_id)
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")

    # Nach Pfad sortieren, nicht nach Name: es gibt mehrere "Boden 0",
    # und untereinander ergeben sie nur mit ihrem Pfad einen Sinn.
    ziele = []
    for kandidat in db.query(Location).all():
        if kandidat.id == loc.id or kandidat.id == loc.parent_id:
            continue
        if loc.type not in VALID_CHILDREN.get(kandidat.type, []):
            continue
        if ist_nachfahre(db, kandidat.id, loc.id):
            continue
        ziele.append(build_location_response(kandidat, db))

    ziele.sort(key=lambda z: (z["breadcrumb"] or z["name"]).lower())

    if loc.parent_id is not None and loc.type in VALID_CHILDREN[None]:
        ziele.insert(0, {
            "id": 0, "name": "Oberste Ebene", "description": None,
            "type": "sonstiges", "storage_mode": "both",
            "coordinate_x": None, "coordinate_y": None, "coordinate_z": None,
            "parent_id": None, "created_at": loc.created_at,
            "item_count": 0, "breadcrumb": "",
        })
    return ziele


@router.patch("/{location_id}/verschiebe", response_model=LocationResponse)
def verschiebe_location(
    location_id: int,
    ziel_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(current_admin),
):
    """Haengt einen Ort samt Inhalt unter einen anderen Elternort.

    ziel_id 0 bedeutet oberste Ebene. Die enthaltenen Gegenstaende ziehen
    automatisch mit -- sie haengen am Ort, nicht am Pfad.
    """
    loc = db.get(Location, location_id)
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")

    neuer_parent_id = None if ziel_id == 0 else ziel_id
    ziel = pruefe_verschiebung(db, loc, neuer_parent_id)
    validate_type(ziel, loc.type)

    loc.parent_id = neuer_parent_id
    # ans Ende der neuen Geschwister setzen
    geschwister = [g for g in sorted_siblings(db, neuer_parent_id) if g.id != loc.id]
    loc.sort_order = (geschwister[-1].sort_order + 10) if geschwister else 0
    db.commit()
    db.refresh(loc)
    return build_location_response(loc, db)
