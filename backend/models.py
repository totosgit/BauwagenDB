import uuid

from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, DateTime, Boolean, Table
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship
from datetime import datetime, timezone

from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID
from fastapi_users_db_sqlalchemy.access_token import SQLAlchemyBaseAccessTokenTableUUID
from fastapi_users_db_sqlalchemy.generics import GUID

from database import Base

def now():
    return datetime.now(timezone.utc)

class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    type = Column(String(50), default="kiste")  # regal, kiste, fach, wand, boden, fahrzeug, sonstiges
    storage_mode = Column(String(10), default="both", server_default="both")  # lager | jahr | both
    coordinate_x = Column(Float, nullable=True)
    coordinate_y = Column(Float, nullable=True)
    coordinate_z = Column(Float, nullable=True)
    parent_id = Column(Integer, ForeignKey("locations.id", ondelete="SET NULL"), nullable=True)
    # Eine Kiste kann unter dem Jahr woanders stehen als auf dem Lager.
    # Leer = sie steht immer am selben Platz. Gegenstaende darin ziehen
    # automatisch mit: sie bleiben in der Kiste, nur die Kiste wandert.
    parent_jahr_id = Column(Integer, ForeignKey("locations.id", ondelete="SET NULL"), nullable=True)
    sort_order = Column(Integer, default=0, server_default="0")
    created_at = Column(DateTime, default=now)

    parent = relationship("Location", remote_side=[id], foreign_keys=[parent_id], back_populates="children")
    children = relationship(
        "Location", back_populates="parent", cascade="all, delete-orphan",
        foreign_keys=[parent_id],
        order_by="Location.sort_order, Location.id",
    )


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True, index=True)
    quantity = Column(Float, default=1)
    unit = Column(String(50), default="Stück")
    storage_mode = Column(String(10), default="both", server_default="both")
    location_lager_id = Column(Integer, ForeignKey("locations.id", ondelete="SET NULL"), nullable=True)
    location_jahr_id  = Column(Integer, ForeignKey("locations.id", ondelete="SET NULL"), nullable=True)
    aufgebaut       = Column(Boolean, default=False, server_default="0")
    aufgebaut_notiz = Column(Text, nullable=True)
    image_path = Column(String(500), nullable=True)
    tags = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=now)
    updated_at = Column(DateTime, default=now, onupdate=now)

    location_lager = relationship("Location", foreign_keys=[location_lager_id])
    location_jahr  = relationship("Location", foreign_keys=[location_jahr_id])


class Drink(Base):
    __tablename__ = "drinks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=True)   # Softdrink, Wasser, Saft, Bier, ...
    emoji = Column(String(10), nullable=True)
    price = Column(Float, nullable=True)
    price_gl = Column(Float, nullable=True)         # GL-Preis (None = kostenlos für GL)
    stock_lager = Column(Integer, default=0)        # Bestand auf dem Lager
    created_at = Column(DateTime, default=now)

    tallies = relationship("Tally", back_populates="drink", cascade="all, delete-orphan")


# Zuordnung User <-> Gruppe. Gruppen sind rein beschreibend (Kueche,
# Bauwagentrupp, ...) und haben bewusst keinerlei Rechtewirkung.
user_groups = Table(
    "user_groups",
    Base.metadata,
    Column("user_id", GUID, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("group_id", Integer, ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True),
)


class User(SQLAlchemyBaseUserTableUUID, Base):
    """Benutzerkonto. Login laeuft ueber username, nicht ueber E-Mail.

    is_active  = vom Admin freigegeben (Registrierung legt False an)
    is_superuser = Admin
    """
    __tablename__ = "users"

    username     = Column(String(50), unique=True, index=True, nullable=False)
    display_name = Column(String(100), nullable=False)
    # E-Mail ist bei uns optional -- die Basisklasse verlangt sie sonst zwingend.
    email: Mapped[str | None] = mapped_column(String(320), unique=True, nullable=True)
    created_at   = Column(DateTime, default=now)

    groups  = relationship("Group", secondary=user_groups, back_populates="members", lazy="selectin")
    tallies = relationship("Tally", back_populates="user", cascade="all, delete-orphan")


class AccessToken(SQLAlchemyBaseAccessTokenTableUUID, Base):
    """Login-Session. Wird von fastapi-users' DatabaseStrategy verwaltet."""
    __tablename__ = "access_tokens"

    # Basisklasse zeigt auf "user.id" -- unsere Tabelle heisst "users".
    @declared_attr
    def user_id(cls) -> Mapped[uuid.UUID]:
        return mapped_column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)


class Group(Base):
    """Frei anlegbare Zugehoerigkeit, z.B. Kueche oder Bauwagentrupp.

    Dient nur der Charakterisierung im Profil, vergibt keine Rechte.
    """
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    emoji = Column(String(10), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=now)

    members = relationship("User", secondary=user_groups, back_populates="groups")


class Note(Base):
    """Notiz für den Bauwagen.

    Der Name kommt jetzt aus dem Konto (created_by). Das alte Freitextfeld
    author bleibt erhalten, damit Notizen von vor der Konten-Umstellung
    ihren Namen behalten -- nachtraeglich zuordnen waere geraten.
    """
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    author = Column(String(100), nullable=True)
    created_by = Column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=now)

    urheber = relationship("User", foreign_keys=[created_by])


class ShoppingItem(Base):
    """Einkaufsliste - Dinge die besorgt werden müssen."""
    __tablename__ = "shopping_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    quantity = Column(Float, default=1)
    unit = Column(String(50), default="Stück")
    urgency = Column(String(20), default="mittel")  # niedrig | mittel | hoch | dringend
    item_id = Column(Integer, ForeignKey("items.id", ondelete="SET NULL"), nullable=True)
    # Verweis aufs Konto plus Name als Momentaufnahme: so bleibt sichtbar,
    # wer es aufgeschrieben hat, auch wenn das Konto später gelöscht wird.
    created_by = Column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    author = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    erledigt = Column(Boolean, default=False, server_default="0")
    created_at = Column(DateTime, default=now)

    item = relationship("Item", foreign_keys=[item_id])
    urheber = relationship("User", foreign_keys=[created_by])


class Tally(Base):
    """Einzelner Strich: ein Benutzer hat sich ein Getränk genommen.

    Striche setzt und loescht jeder nur fuer sich selbst.
    """
    __tablename__ = "tallies"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    drink_id = Column(Integer, ForeignKey("drinks.id", ondelete="CASCADE"), nullable=False)
    count = Column(Integer, default=1)
    created_at = Column(DateTime, default=now)

    user = relationship("User", back_populates="tallies")
    drink = relationship("Drink", back_populates="tallies")


class Einstellung(Base):
    """Anwendungsweite Einstellungen als Schluessel-Wert-Paare.

    Bewusst generisch statt einer Spalte je Einstellung: es sind wenige,
    sie aendern sich selten, und so braucht jede neue keine Migration.
    """
    __tablename__ = "einstellungen"

    schluessel = Column(String(50), primary_key=True)
    wert = Column(Text, nullable=True)
    geaendert_am = Column(DateTime, default=now, onupdate=now)
