from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import current_user
from database import get_db
from models import ShoppingItem, User
from schemas import ShoppingItemCreate, ShoppingItemUpdate, ShoppingItemResponse

URGENCY_ORDER = {"dringend": 0, "hoch": 1, "mittel": 2, "niedrig": 3}

router = APIRouter(prefix="/shopping", tags=["shopping"])


def _to_response(item: ShoppingItem) -> dict:
    """Der angezeigte Name kommt bevorzugt aus dem Konto.

    Ist das Konto weg oder stammt der Eintrag aus der Zeit vor den Konten,
    greift der gespeicherte Name -- sonst "unbekannt".
    """
    urheber = item.urheber
    return {
        "id": item.id,
        "name": item.name,
        "quantity": item.quantity,
        "unit": item.unit,
        "urgency": item.urgency,
        "item_id": item.item_id,
        "notes": item.notes,
        "erledigt": item.erledigt,
        "created_at": item.created_at,
        "author": (urheber.display_name if urheber else None) or item.author or "unbekannt",
        "created_by": item.created_by,
    }


@router.get("/", response_model=list[ShoppingItemResponse])
def list_shopping(db: Session = Depends(get_db), _: User = Depends(current_user)):
    items = db.query(ShoppingItem).all()
    items.sort(key=lambda x: (x.erledigt, URGENCY_ORDER.get(x.urgency, 99), x.created_at))
    return [_to_response(i) for i in items]


@router.post("/", response_model=ShoppingItemResponse, status_code=201)
def create_shopping_item(
    data: ShoppingItemCreate,
    db: Session = Depends(get_db),
    me: User = Depends(current_user),
):
    item = ShoppingItem(
        name=data.name.strip(),
        quantity=data.quantity,
        unit=data.unit,
        urgency=data.urgency,
        item_id=data.item_id,
        notes=data.notes,
        created_by=me.id,
        author=me.display_name,  # Momentaufnahme, ueberlebt Kontoloeschung
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return _to_response(item)


@router.patch("/{item_id}", response_model=ShoppingItemResponse)
def update_shopping_item(
    item_id: int,
    data: ShoppingItemUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(current_user),
):
    item = db.get(ShoppingItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Nicht gefunden")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return _to_response(item)


@router.delete("/{item_id}", status_code=204)
def delete_shopping_item(
    item_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(current_user),
):
    item = db.get(ShoppingItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Nicht gefunden")
    db.delete(item)
    db.commit()


@router.delete("/", status_code=204)
def clear_erledigt(db: Session = Depends(get_db), _: User = Depends(current_user)):
    """Alle erledigten Einträge löschen."""
    db.query(ShoppingItem).filter(ShoppingItem.erledigt == True).delete()  # noqa: E712
    db.commit()
