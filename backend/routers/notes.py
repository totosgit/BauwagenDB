from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import current_user
from database import get_db
from models import Note, User
from schemas import NoteCreate, NoteResponse

router = APIRouter(prefix="/notes", tags=["notes"])


def _to_response(note: Note) -> dict:
    """Der angezeigte Name kommt bevorzugt aus dem Konto.

    Ist das Konto weg oder stammt die Notiz aus der Zeit vor den Konten,
    greift der gespeicherte Name.
    """
    urheber = note.urheber
    return {
        "id": note.id,
        "author": (urheber.display_name if urheber else None) or note.author or "unbekannt",
        "created_by": note.created_by,
        "text": note.text,
        "created_at": note.created_at,
    }


@router.get("/", response_model=list[NoteResponse])
def list_notes(db: Session = Depends(get_db), _: User = Depends(current_user)):
    notes = db.query(Note).order_by(Note.created_at.desc()).all()
    return [_to_response(n) for n in notes]


@router.post("/", response_model=NoteResponse, status_code=201)
def create_note(
    data: NoteCreate,
    db: Session = Depends(get_db),
    me: User = Depends(current_user),
):
    note = Note(
        text=data.text.strip(),
        created_by=me.id,
        author=me.display_name,  # Momentaufnahme, ueberlebt Kontoloeschung
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return _to_response(note)


@router.delete("/{note_id}", status_code=204)
def delete_note(
    note_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(current_user),
):
    """Die Notizen sind eine gemeinsame Pinnwand -- abräumen darf jeder."""
    note = db.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Notiz nicht gefunden")
    db.delete(note)
    db.commit()
