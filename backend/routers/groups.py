"""Gruppen wie Küche, Gruppenleiter oder Bauwagentrupp.

Wichtig: Gruppen sind reine Charakterisierung fuers Profil. Sie vergeben
keinerlei Rechte -- Berechtigungen haengen ausschliesslich an is_superuser.
Anlegen und Loeschen darf ein Admin, beitreten und austreten jeder selbst.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import current_admin, current_user
from database import get_db
from models import Group, User
from schemas import GroupCreate, GroupResponse, GroupUpdate, UserPublic

router = APIRouter(prefix="/groups", tags=["groups"])


def _to_response(group: Group, user: User) -> dict:
    return {
        "id": group.id,
        "name": group.name,
        "emoji": group.emoji,
        "description": group.description,
        "member_count": len(group.members),
        "is_member": any(m.id == user.id for m in group.members),
    }


def _get_group_or_404(db: Session, group_id: int) -> Group:
    group = db.get(Group, group_id)
    if group is None:
        raise HTTPException(status_code=404, detail="Gruppe nicht gefunden")
    return group


@router.get("/", response_model=list[GroupResponse])
def list_groups(db: Session = Depends(get_db), user: User = Depends(current_user)):
    groups = db.query(Group).order_by(Group.name).all()
    return [_to_response(g, user) for g in groups]


@router.post("/", response_model=GroupResponse, status_code=201)
def create_group(
    data: GroupCreate,
    db: Session = Depends(get_db),
    user: User = Depends(current_admin),
):
    name = data.name.strip()
    if db.query(Group).filter(Group.name == name).first():
        raise HTTPException(status_code=409, detail="Diese Gruppe gibt es schon")

    group = Group(name=name, emoji=data.emoji, description=data.description)
    db.add(group)
    db.commit()
    db.refresh(group)
    return _to_response(group, user)


@router.patch("/{group_id}", response_model=GroupResponse)
def update_group(
    group_id: int,
    data: GroupUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(current_admin),
):
    group = _get_group_or_404(db, group_id)

    if data.name is not None:
        name = data.name.strip()
        clash = db.query(Group).filter(Group.name == name, Group.id != group_id).first()
        if clash:
            raise HTTPException(status_code=409, detail="Diese Gruppe gibt es schon")
        group.name = name
    if data.emoji is not None:
        group.emoji = data.emoji
    if data.description is not None:
        group.description = data.description

    db.commit()
    db.refresh(group)
    return _to_response(group, user)


@router.delete("/{group_id}", status_code=204)
def delete_group(
    group_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(current_admin),
):
    group = _get_group_or_404(db, group_id)
    db.delete(group)
    db.commit()


@router.get("/{group_id}/members", response_model=list[UserPublic])
def list_members(
    group_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(current_user),
):
    group = _get_group_or_404(db, group_id)
    return sorted(group.members, key=lambda u: u.display_name)


@router.post("/{group_id}/join", response_model=GroupResponse)
def join_group(
    group_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    group = _get_group_or_404(db, group_id)
    if not any(m.id == user.id for m in group.members):
        group.members.append(user)
        db.commit()
        db.refresh(group)
    return _to_response(group, user)


@router.delete("/{group_id}/join", response_model=GroupResponse)
def leave_group(
    group_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    group = _get_group_or_404(db, group_id)
    member = next((m for m in group.members if m.id == user.id), None)
    if member is not None:
        group.members.remove(member)
        db.commit()
        db.refresh(group)
    return _to_response(group, user)


@router.put("/{group_id}/members/{user_id}", response_model=GroupResponse)
def admin_add_member(
    group_id: int,
    user_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(current_admin),
):
    group = _get_group_or_404(db, group_id)
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="Benutzer nicht gefunden")
    if not any(m.id == target.id for m in group.members):
        group.members.append(target)
        db.commit()
        db.refresh(group)
    return _to_response(group, admin)


@router.delete("/{group_id}/members/{user_id}", response_model=GroupResponse)
def admin_remove_member(
    group_id: int,
    user_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(current_admin),
):
    group = _get_group_or_404(db, group_id)
    member = next((m for m in group.members if str(m.id) == str(user_id)), None)
    if member is not None:
        group.members.remove(member)
        db.commit()
        db.refresh(group)
    return _to_response(group, admin)
