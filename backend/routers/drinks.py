from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Drink
from schemas import DrinkCreate, DrinkUpdate, DrinkResponse

router = APIRouter(prefix="/drinks", tags=["drinks"])


@router.get("/", response_model=list[DrinkResponse])
def list_drinks(db: Session = Depends(get_db)):
    return db.query(Drink).order_by(Drink.category, Drink.name).all()


@router.post("/", response_model=DrinkResponse, status_code=201)
def create_drink(data: DrinkCreate, db: Session = Depends(get_db)):
    drink = Drink(**data.model_dump())
    db.add(drink)
    db.commit()
    db.refresh(drink)
    return drink


@router.put("/{drink_id}", response_model=DrinkResponse)
def update_drink(drink_id: int, data: DrinkUpdate, db: Session = Depends(get_db)):
    drink = db.get(Drink, drink_id)
    if not drink:
        raise HTTPException(status_code=404, detail="Drink not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(drink, field, value)
    db.commit()
    db.refresh(drink)
    return drink


@router.delete("/{drink_id}", status_code=204)
def delete_drink(drink_id: int, db: Session = Depends(get_db)):
    drink = db.get(Drink, drink_id)
    if not drink:
        raise HTTPException(status_code=404, detail="Drink not found")
    db.delete(drink)
    db.commit()


@router.post("/{drink_id}/deduct", response_model=DrinkResponse)
def deduct_drink(drink_id: int, amount: int = 1, db: Session = Depends(get_db)):
    drink = db.get(Drink, drink_id)
    if not drink:
        raise HTTPException(status_code=404, detail="Drink not found")
    if drink.stock_lager < amount:
        raise HTTPException(status_code=400, detail="Bestand reicht nicht aus")
    drink.stock_lager -= amount
    db.commit()
    db.refresh(drink)
    return drink


@router.post("/{drink_id}/restock", response_model=DrinkResponse)
def restock_drink(drink_id: int, amount: int = 1, db: Session = Depends(get_db)):
    drink = db.get(Drink, drink_id)
    if not drink:
        raise HTTPException(status_code=404, detail="Drink not found")
    drink.stock_lager += amount
    db.commit()
    db.refresh(drink)
    return drink
