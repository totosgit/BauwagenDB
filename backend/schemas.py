import uuid
from pydantic import BaseModel, EmailStr, Field
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


# --- Gruppen (rein beschreibend, ohne Rechtewirkung) ---

class GroupCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    emoji: Optional[str] = None
    description: Optional[str] = None


class GroupUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    emoji: Optional[str] = None
    description: Optional[str] = None


class GroupBadge(BaseModel):
    """Gruppe wie sie als Label im Profil erscheint."""
    id: int
    name: str
    emoji: Optional[str] = None

    model_config = {"from_attributes": True}


class GroupResponse(GroupBadge):
    description: Optional[str] = None
    member_count: int = 0
    is_member: bool = False


# --- Benutzer ---

class UserRegister(BaseModel):
    username: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_.-]+$")
    display_name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8)
    email: Optional[EmailStr] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class UserPublic(BaseModel):
    """Profil wie es andere Benutzer sehen."""
    id: uuid.UUID
    username: str
    display_name: str
    is_superuser: bool
    groups: List[GroupBadge] = []
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserMe(UserPublic):
    email: Optional[str] = None
    is_active: bool = True


class UserUpdateSelf(BaseModel):
    display_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(default=None, min_length=8)
    # Beim Passwortwechsel Pflicht -- verhindert, dass ein fremdes offenes
    # Geraet einfach das Passwort ueberschreiben kann.
    current_password: Optional[str] = None


class UserAdminUpdate(BaseModel):
    """Nur fuer Admins: freigeben, sperren, Adminrechte vergeben."""
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    display_name: Optional[str] = Field(default=None, min_length=1, max_length=100)


class PasswordReset(BaseModel):
    password: str = Field(min_length=8)


# --- Strichliste ---

class TallyCreate(BaseModel):
    drink_id: int
    count: int = 1


class TallyResponse(BaseModel):
    id: int
    user_id: uuid.UUID
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
    user_id: uuid.UUID
    username: str
    display_name: str
    entries: List[TallySummaryEntry]
    grand_total: int
    is_self: bool = False


# --- Einkaufsliste ---

class ShoppingItemCreate(BaseModel):
    name: str
    quantity: float = 1
    unit: str = "Stück"
    urgency: str = "mittel"
    item_id: Optional[int] = None
    notes: Optional[str] = None


class ShoppingItemUpdate(BaseModel):
    name: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    urgency: Optional[str] = None
    notes: Optional[str] = None
    erledigt: Optional[bool] = None


class ShoppingItemResponse(BaseModel):
    id: int
    name: str
    quantity: float
    unit: str
    urgency: str
    item_id: Optional[int] = None
    notes: Optional[str] = None
    erledigt: bool
    created_at: datetime
    # Wer hat es aufgeschrieben
    author: str = "unbekannt"
    created_by: Optional[uuid.UUID] = None

    model_config = {"from_attributes": True}


# --- Notizen ---

class NoteCreate(BaseModel):
    # Der Name kommt aus dem angemeldeten Konto, nicht aus dem Formular.
    text: str = Field(min_length=1, max_length=2000)


class NoteResponse(BaseModel):
    id: int
    author: str
    created_by: Optional[uuid.UUID] = None
    text: str
    created_at: datetime

    model_config = {"from_attributes": True}
