import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import func
from sqlalchemy.orm import Session

from auth import current_admin, current_user
from database import get_db, IMAGES_DIR
from models import Item, User
from schemas import ItemCreate, ItemUpdate, ItemResponse
from utils import alle_breadcrumbs, get_breadcrumb, ort_mit_nachfahren

router = APIRouter(prefix="/items", tags=["items"])

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}


def item_to_response(
    item: Item,
    db: Session,
    pfade: dict[int, str] | None = None,
    pfade_jahr: dict[int, str] | None = None,
) -> dict:
    """pfade / pfade_jahr = vorab geladene Lagerort-Pfade je Modus. Ohne sie
    wird pro Gegenstand einzeln aufgeloest -- fuer Listen immer die
    Sammelvariante nutzen.

    Zwei Saetze, weil eine Kiste unter dem Jahr woanders stehen kann und
    der Pfad dann anders lautet, obwohl der Gegenstand in derselben Kiste
    liegt."""
    def pfad(oid, jahr=False):
        tabelle = pfade_jahr if jahr else pfade
        if tabelle is not None:
            return tabelle.get(oid, "")
        return get_breadcrumb(db, oid, "jahr" if jahr else "lager")

    return {
        "id": item.id,
        "name": item.name,
        "description": item.description,
        "category": item.category,
        "quantity": item.quantity,
        "unit": item.unit,
        "storage_mode": item.storage_mode,
        "location_lager_id": item.location_lager_id,
        "location_jahr_id": item.location_jahr_id,
        "aufgebaut": item.aufgebaut,
        "aufgebaut_notiz": item.aufgebaut_notiz,
        "image_path": item.image_path,
        "tags": item.tags,
        "notes": item.notes,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
        "breadcrumb_lager": pfad(item.location_lager_id),
        "breadcrumb_jahr": pfad(item.location_jahr_id, jahr=True),
    }


@router.get("/", response_model=list[ItemResponse])
def list_items(
    category: str | None = None,
    mode: str | None = None,
    location_id: int | None = None,
    db: Session = Depends(get_db),
):
    """location_id zeigt ausschliesslich, was an diesem Ort liegt --
    einschliesslich allem, was darunter haengt. Welche Ortsspalte zaehlt,
    haengt vom Modus ab: unter dem Jahr kann eine Kiste woanders stehen."""
    q = db.query(Item)
    if category:
        q = q.filter(Item.category == category)
    if mode:
        q = q.filter(Item.storage_mode.in_([mode, "both"]))
    if location_id is not None:
        ids = ort_mit_nachfahren(db, location_id, mode or "lager")
        spalte = Item.location_jahr_id if mode == "jahr" else Item.location_lager_id
        q = q.filter(spalte.in_(ids))
    items = q.order_by(Item.name).all()
    pfade = alle_breadcrumbs(db, "lager")
    pfade_jahr = alle_breadcrumbs(db, "jahr")
    return [item_to_response(i, db, pfade, pfade_jahr) for i in items]


@router.get("/categories", response_model=list[str])
def list_categories(db: Session = Depends(get_db)):
    rows = db.query(Item.category).filter(Item.category != None).distinct().all()  # noqa: E711
    return sorted([r[0] for r in rows if r[0]])


@router.get("/categories/stats")
def category_stats(db: Session = Depends(get_db), _: User = Depends(current_user)):
    """Kategorien mit Anzahl -- Grundlage fuer die Verwaltung."""
    rows = (
        db.query(Item.category, func.count(Item.id))
        .filter(Item.category != None)  # noqa: E711
        .group_by(Item.category)
        .all()
    )
    return sorted(
        [{"name": n, "anzahl": a} for n, a in rows if n],
        key=lambda k: k["name"].lower(),
    )


@router.patch("/categories/{name}")
def rename_category(
    name: str,
    neu: str,
    db: Session = Depends(get_db),
    _: User = Depends(current_admin),
):
    """Benennt eine Kategorie um. Gibt es das Ziel schon, werden beide
    zusammengefuehrt -- Kategorien sind ein Textfeld am Gegenstand, keine
    eigene Tabelle."""
    neu = neu.strip()
    if not neu:
        raise HTTPException(status_code=400, detail="Der neue Name darf nicht leer sein")
    betroffen = db.query(Item).filter(Item.category == name).update(
        {"category": neu}, synchronize_session=False
    )
    db.commit()
    if betroffen == 0:
        raise HTTPException(status_code=404, detail="Kategorie nicht gefunden")
    return {"umbenannt": betroffen, "von": name, "nach": neu}


@router.delete("/categories/{name}", status_code=204)
def delete_category(
    name: str,
    db: Session = Depends(get_db),
    _: User = Depends(current_admin),
):
    """Entfernt die Kategorie von allen Gegenstaenden. Die Gegenstaende
    selbst bleiben, sie sind danach nur ohne Kategorie."""
    db.query(Item).filter(Item.category == name).update(
        {"category": None}, synchronize_session=False
    )
    db.commit()


@router.get("/tags", response_model=list[str])
def list_tags(db: Session = Depends(get_db), _: User = Depends(current_user)):
    """Alle bereits vergebenen Tags -- fuer die Vorschlaege im Formular.

    Tags stehen kommagetrennt in einem Textfeld, deshalb hier aufteilen
    und Dubletten entfernen (ohne Ruecksicht auf Gross-/Kleinschreibung).
    """
    gesehen: dict[str, str] = {}
    for (roh,) in db.query(Item.tags).filter(Item.tags != None).all():  # noqa: E711
        for teil in (roh or "").split(","):
            t = teil.strip()
            if t:
                gesehen.setdefault(t.lower(), t)
    return sorted(gesehen.values(), key=str.lower)


@router.get("/{item_id}", response_model=ItemResponse)
def get_item(item_id: int, db: Session = Depends(get_db)):
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item_to_response(item, db)


@router.post("/", response_model=ItemResponse, status_code=201)
def create_item(data: ItemCreate, db: Session = Depends(get_db)):
    item = Item(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item_to_response(item, db)


@router.put("/{item_id}", response_model=ItemResponse)
def update_item(item_id: int, data: ItemUpdate, db: Session = Depends(get_db)):
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item_to_response(item, db)


@router.delete("/{item_id}", status_code=204)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if item.image_path:
        full_path = os.path.join(IMAGES_DIR, item.image_path)
        if os.path.exists(full_path):
            os.remove(full_path)
    db.delete(item)
    db.commit()


@router.post("/{item_id}/image", response_model=ItemResponse)
async def upload_image(item_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, WEBP images are allowed")

    if item.image_path:
        old_path = os.path.join(IMAGES_DIR, item.image_path)
        if os.path.exists(old_path):
            os.remove(old_path)

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "jpg"
    filename = f"{uuid.uuid4().hex}.{ext}"
    dest = os.path.join(IMAGES_DIR, filename)

    contents = await file.read()
    with open(dest, "wb") as f:
        f.write(contents)

    item.image_path = filename
    db.commit()
    db.refresh(item)
    return item_to_response(item, db)


@router.delete("/{item_id}/image", response_model=ItemResponse)
def delete_image(item_id: int, db: Session = Depends(get_db)):
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if item.image_path:
        full_path = os.path.join(IMAGES_DIR, item.image_path)
        if os.path.exists(full_path):
            os.remove(full_path)
        item.image_path = None
        db.commit()
        db.refresh(item)
    return item_to_response(item, db)
