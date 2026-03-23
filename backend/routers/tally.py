from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models import GroupLeader, Tally, Drink
from schemas import GroupLeaderCreate, GroupLeaderResponse, TallyCreate, TallyResponse, TallySummary, TallySummaryEntry

router = APIRouter(tags=["tally"])


# --- Gruppenleiter ---

@router.get("/group-leaders/", response_model=list[GroupLeaderResponse])
def list_group_leaders(db: Session = Depends(get_db)):
    return db.query(GroupLeader).order_by(GroupLeader.name).all()


@router.post("/group-leaders/", response_model=GroupLeaderResponse, status_code=201)
def create_group_leader(data: GroupLeaderCreate, db: Session = Depends(get_db)):
    gl = GroupLeader(name=data.name)
    db.add(gl)
    db.commit()
    db.refresh(gl)
    return gl


@router.delete("/group-leaders/{gl_id}", status_code=204)
def delete_group_leader(gl_id: int, db: Session = Depends(get_db)):
    gl = db.get(GroupLeader, gl_id)
    if not gl:
        raise HTTPException(status_code=404, detail="Gruppenleiter nicht gefunden")
    db.delete(gl)
    db.commit()


# --- Strichliste ---

@router.get("/tally/summary/{gl_id}", response_model=TallySummary)
def get_tally_summary(gl_id: int, db: Session = Depends(get_db)):
    gl = db.get(GroupLeader, gl_id)
    if not gl:
        raise HTTPException(status_code=404, detail="Gruppenleiter nicht gefunden")

    rows = (
        db.query(Tally.drink_id, func.sum(Tally.count).label("total"))
        .filter(Tally.group_leader_id == gl_id)
        .group_by(Tally.drink_id)
        .all()
    )

    entries = []
    grand_total = 0
    for drink_id, total in rows:
        drink = db.get(Drink, drink_id)
        entries.append(TallySummaryEntry(
            drink_id=drink_id,
            drink_name=drink.name if drink else "?",
            drink_emoji=drink.emoji if drink else None,
            total=total,
        ))
        grand_total += total

    return TallySummary(
        group_leader_id=gl_id,
        group_leader_name=gl.name,
        entries=entries,
        grand_total=grand_total,
    )


@router.get("/tally/all-summaries/", response_model=list[TallySummary])
def get_all_summaries(db: Session = Depends(get_db)):
    """Übersicht aller Gruppenleiter mit ihren Tallys."""
    leaders = db.query(GroupLeader).order_by(GroupLeader.name).all()
    result = []
    for gl in leaders:
        rows = (
            db.query(Tally.drink_id, func.sum(Tally.count).label("total"))
            .filter(Tally.group_leader_id == gl.id)
            .group_by(Tally.drink_id)
            .all()
        )
        entries = []
        grand_total = 0
        for drink_id, total in rows:
            drink = db.get(Drink, drink_id)
            entries.append(TallySummaryEntry(
                drink_id=drink_id,
                drink_name=drink.name if drink else "?",
                drink_emoji=drink.emoji if drink else None,
                total=total,
            ))
            grand_total += total
        result.append(TallySummary(
            group_leader_id=gl.id,
            group_leader_name=gl.name,
            entries=entries,
            grand_total=grand_total,
        ))
    return result


@router.post("/tally/", response_model=TallyResponse, status_code=201)
def add_tally(data: TallyCreate, db: Session = Depends(get_db)):
    if not db.get(GroupLeader, data.group_leader_id):
        raise HTTPException(status_code=404, detail="Gruppenleiter nicht gefunden")
    if not db.get(Drink, data.drink_id):
        raise HTTPException(status_code=404, detail="Getränk nicht gefunden")
    tally = Tally(**data.model_dump())
    db.add(tally)
    db.commit()
    db.refresh(tally)
    return tally


@router.delete("/tally/{tally_id}", status_code=204)
def delete_tally(tally_id: int, db: Session = Depends(get_db)):
    """Einzelnen Strich löschen (Korrektur)."""
    tally = db.get(Tally, tally_id)
    if not tally:
        raise HTTPException(status_code=404, detail="Tally nicht gefunden")
    db.delete(tally)
    db.commit()


@router.delete("/tally/reset/{gl_id}", status_code=204)
def reset_tallies(gl_id: int, db: Session = Depends(get_db)):
    """Alle Striche eines Gruppenleiters löschen (Abrechnung)."""
    db.query(Tally).filter(Tally.group_leader_id == gl_id).delete()
    db.commit()
