from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import ShoppingItem
from schemas import ShoppingItemCreate, ShoppingItemUpdate, ShoppingItemResponse

URGENCY_ORDER = {"dringend": 0, "hoch": 1, "mittel": 2, "niedrig": 3}

router = APIRouter(prefix="/shopping", tags=["shopping"])


@router.get("/", response_model=list[ShoppingItemResponse])
def list_shopping(db: Session = Depends(get_db)):
    items = db.query(ShoppingItem).all()
    return sorted(items, key=lambda x: (x.erledigt, URGENCY_ORDER.get(x.urgency, 99), x.created_at))


@router.post("/", response_model=ShoppingItemResponse, status_code=201)
def create_shopping_item(data: ShoppingItemCreate, db: Session = Depends(get_db)):
    item = ShoppingItem(
        name=data.name.strip(),
        quantity=data.quantity,
        unit=data.unit,
        urgency=data.urgency,
        item_id=data.item_id,
        notes=data.notes,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/{item_id}", response_model=ShoppingItemResponse)
def update_shopping_item(item_id: int, data: ShoppingItemUpdate, db: Session = Depends(get_db)):
    item = db.get(ShoppingItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Nicht gefunden")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=204)
def delete_shopping_item(item_id: int, db: Session = Depends(get_db)):
    item = db.get(ShoppingItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Nicht gefunden")
    db.delete(item)
    db.commit()


@router.delete("/", status_code=204)
def clear_erledigt(db: Session = Depends(get_db)):
    """Alle erledigten Einträge löschen."""
    db.query(ShoppingItem).filter(ShoppingItem.erledigt == True).delete()
    db.commit()
