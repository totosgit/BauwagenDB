from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Note
from schemas import NoteCreate, NoteResponse

router = APIRouter(prefix="/notes", tags=["notes"])


@router.get("/", response_model=list[NoteResponse])
def list_notes(db: Session = Depends(get_db)):
    return db.query(Note).order_by(Note.created_at.desc()).all()


@router.post("/", response_model=NoteResponse, status_code=201)
def create_note(data: NoteCreate, db: Session = Depends(get_db)):
    note = Note(author=data.author.strip(), text=data.text.strip())
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@router.delete("/{note_id}", status_code=204)
def delete_note(note_id: int, db: Session = Depends(get_db)):
    note = db.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Notiz nicht gefunden")
    db.delete(note)
    db.commit()
