from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
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
    sort_order = Column(Integer, default=0, server_default="0")
    created_at = Column(DateTime, default=now)

    parent = relationship("Location", remote_side=[id], back_populates="children")
    children = relationship(
        "Location", back_populates="parent", cascade="all, delete-orphan",
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


class GroupLeader(Base):
    __tablename__ = "group_leaders"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=now)

    tallies = relationship("Tally", back_populates="group_leader", cascade="all, delete-orphan")


class Session(Base):
    """Login-Session mit sliding expiry."""
    __tablename__ = "sessions"

    token = Column(String(64), primary_key=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())


class Note(Base):
    """Notiz mit Autorenname für den Bauwagen."""
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    author = Column(String(100), nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=now)


class Tally(Base):
    """Einzelner Strich: ein Gruppenleiter hat ein Getränk genommen."""
    __tablename__ = "tallies"

    id = Column(Integer, primary_key=True, index=True)
    group_leader_id = Column(Integer, ForeignKey("group_leaders.id", ondelete="CASCADE"), nullable=False)
    drink_id = Column(Integer, ForeignKey("drinks.id", ondelete="CASCADE"), nullable=False)
    count = Column(Integer, default=1)
    created_at = Column(DateTime, default=now)

    group_leader = relationship("GroupLeader", back_populates="tallies")
    drink = relationship("Drink", back_populates="tallies")
