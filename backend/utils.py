from sqlalchemy import or_
from sqlalchemy.orm import Session
from models import Location, Item


def alle_breadcrumbs(db: Session, modus: str = "lager") -> dict[int, str]:
    """Alle Lagerort-Pfade in einer Abfrage.

    Die Einzelvariante get_breadcrumb() laeuft pro Aufruf eine Kette bis zur
    Wurzel. Bei einer Liste mit vielen Gegenstaenden waren das schnell
    hunderte Abfragen -- messbar der langsamste Endpunkt der Anwendung.

    modus: unter dem Jahr zaehlt parent_jahr_id, wo gesetzt. Dadurch
    wandern Gegenstaende automatisch mit ihrer Kiste, ohne dass an jedem
    einzelnen etwas geaendert werden muesste.
    """
    zeilen = db.query(
        Location.id, Location.name, Location.parent_id, Location.parent_jahr_id
    ).all()
    if modus == "jahr":
        orte = {o.id: (o.name, o.parent_jahr_id if o.parent_jahr_id else o.parent_id) for o in zeilen}
    else:
        orte = {o.id: (o.name, o.parent_id) for o in zeilen}
    fertig: dict[int, str] = {}

    def pfad(oid: int | None) -> str:
        if oid is None or oid not in orte:
            return ""
        if oid in fertig:
            return fertig[oid]
        name, parent = orte[oid]
        fertig[oid] = name          # Zyklenschutz: erst belegen, dann aufloesen
        oben = pfad(parent)
        fertig[oid] = f"{oben} \u203a {name}" if oben else name
        return fertig[oid]

    for oid in orte:
        pfad(oid)
    return fertig


def get_breadcrumb(db: Session, location_id: int | None, modus: str = "lager") -> str:
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
        if modus == "jahr" and loc.parent_jahr_id:
            current_id = loc.parent_jahr_id
        else:
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
        "parent_jahr_id": loc.parent_jahr_id,
        "created_at": loc.created_at,
        "item_count": item_count,
        "breadcrumb": get_breadcrumb(db, loc.id),
        "breadcrumb_jahr": get_breadcrumb(db, loc.id, "jahr"),
    }


def build_location_tree(loc: Location, db: Session) -> dict:
    data = build_location_response(loc, db)
    data["children"] = [build_location_tree(child, db) for child in loc.children]
    return data
