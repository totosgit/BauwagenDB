from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class LocationBase(BaseModel):
    name: str
    description: Optional[str] = None
    type: str = "kiste"
    storage_mode: str = "both"  # lager | jahr | both
    coordinate_x: Optional[float] = None
    coordinate_y: Optional[float] = None
    coordinate_z: Optional[float] = None
    parent_id: Optional[int] = None


class LocationCreate(LocationBase):
    pass


class LocationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    storage_mode: Optional[str] = None
    coordinate_x: Optional[float] = None
    coordinate_y: Optional[float] = None
    coordinate_z: Optional[float] = None
    parent_id: Optional[int] = None


class LocationResponse(LocationBase):
    id: int
    created_at: datetime
    item_count: int = 0
    breadcrumb: str = ""

    model_config = {"from_attributes": True}


class LocationTree(LocationResponse):
    children: List["LocationTree"] = []


class ItemBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    quantity: float = 1
    unit: str = "Stück"
    storage_mode: str = "both"
    location_lager_id: Optional[int] = None
    location_jahr_id:  Optional[int] = None
    aufgebaut:       bool = False
    aufgebaut_notiz: Optional[str] = None
    tags: Optional[str] = None
    notes: Optional[str] = None


class ItemCreate(ItemBase):
    pass


class ItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    storage_mode: Optional[str] = None
    location_lager_id: Optional[int] = None
    location_jahr_id:  Optional[int] = None
    aufgebaut:       Optional[bool] = None
    aufgebaut_notiz: Optional[str] = None
    tags: Optional[str] = None
    notes: Optional[str] = None


class ItemResponse(ItemBase):
    id: int
    image_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    breadcrumb_lager: str = ""
    breadcrumb_jahr:  str = ""

    model_config = {"from_attributes": True}


LocationTree.model_rebuild()


# --- Getränke ---

class DrinkBase(BaseModel):
    name: str
    category: Optional[str] = None
    emoji: Optional[str] = None
    price: Optional[float] = None
    price_gl: Optional[float] = None
    stock_lager: int = 0


class DrinkCreate(DrinkBase):
    pass


class DrinkUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    emoji: Optional[str] = None
    price: Optional[float] = None
    price_gl: Optional[float] = None
    stock_lager: Optional[int] = None


class DrinkResponse(DrinkBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Gruppenleiter ---

class GroupLeaderCreate(BaseModel):
    name: str


class GroupLeaderResponse(BaseModel):
    id: int
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Strichliste ---

class TallyCreate(BaseModel):
    group_leader_id: int
    drink_id: int
    count: int = 1


class TallyResponse(BaseModel):
    id: int
    group_leader_id: int
    drink_id: int
    count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class TallySummaryEntry(BaseModel):
    drink_id: int
    drink_name: str
    drink_emoji: Optional[str] = None
    total: int


class TallySummary(BaseModel):
    group_leader_id: int
    group_leader_name: str
    entries: List[TallySummaryEntry]
    grand_total: int


# --- Notizen ---

class NoteCreate(BaseModel):
    author: str
    text: str


class NoteResponse(BaseModel):
    id: int
    author: str
    text: str
    created_at: datetime

    model_config = {"from_attributes": True}
