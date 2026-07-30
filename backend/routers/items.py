import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from database import get_db, IMAGES_DIR
from models import Item
from schemas import ItemCreate, ItemUpdate, ItemResponse
from utils import alle_breadcrumbs, get_breadcrumb

router = APIRouter(prefix="/items", tags=["items"])

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}


def item_to_response(item: Item, db: Session, pfade: dict[int, str] | None = None) -> dict:
    """pfade = vorab geladene Lagerort-Pfade. Ohne sie wird pro Gegenstand
    einzeln aufgeloest -- fuer Listen immer die Sammelvariante nutzen."""
    def pfad(oid):
        if pfade is not None:
            return pfade.get(oid, "")
        return get_breadcrumb(db, oid)

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
        "breadcrumb_jahr": pfad(item.location_jahr_id),
    }


@router.get("/", response_model=list[ItemResponse])
def list_items(
    category: str | None = None,
    mode: str | None = None,
    db: Session = Depends(get_db)
):
    q = db.query(Item)
    if category:
        q = q.filter(Item.category == category)
    if mode:
        q = q.filter(Item.storage_mode.in_([mode, "both"]))
    items = q.order_by(Item.name).all()
    pfade = alle_breadcrumbs(db)
    return [item_to_response(i, db, pfade) for i in items]


@router.get("/categories", response_model=list[str])
def list_categories(db: Session = Depends(get_db)):
    rows = db.query(Item.category).filter(Item.category != None).distinct().all()
    return sorted([r[0] for r in rows if r[0]])


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
