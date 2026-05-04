from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session as DbSession

from app.db import get_db
from app.models import Attendance, Batch, BatchInvite, BatchStudent, BatchTrainer, Session, User
from app.schemas import (
    BatchCreate,
    BatchInviteRead,
    BatchJoinRead,
    BatchJoinRequest,
    BatchRead,
)
from app.security import require_roles


router = APIRouter(prefix="/batches", tags=["batches"])


def can_manage_batch(user: User, batch: Batch, db: DbSession) -> bool:
    if user.role == "institution":
        return batch.institution_id == user.id
    if user.role == "trainer":
        return db.get(BatchTrainer, {"batch_id": batch.id, "trainer_id": user.id}) is not None
    return False


@router.post("", response_model=BatchRead, status_code=status.HTTP_201_CREATED)
def create_batch(
    payload: BatchCreate,
    db: Annotated[DbSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles("trainer", "institution"))],
) -> Batch:
    institution_id = payload.institution_id
    if current_user.role == "institution":
        institution_id = current_user.id

    batch = Batch(
        name=payload.name,
        institution_id=institution_id,
        programme_id=payload.programme_id,
    )
    db.add(batch)
    db.flush()

    if current_user.role == "trainer":
        db.add(BatchTrainer(batch_id=batch.id, trainer_id=current_user.id))

    db.commit()
    db.refresh(batch)
    return batch


@router.get("/{batch_id}/summary")
def get_batch_summary(
    batch_id: int,
    db: Annotated[DbSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles("institution"))],
) -> dict[str, int]:
    batch = db.get(Batch, batch_id)
    if batch is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found",
        )
    if batch.institution_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Institution cannot access this batch",
        )

    total_students = db.scalar(
        select(func.count(BatchStudent.student_id)).where(BatchStudent.batch_id == batch_id)
    )
    total_sessions = db.scalar(
        select(func.count(Session.id)).where(Session.batch_id == batch_id)
    )
    total_attendance = db.scalar(
        select(func.count(Attendance.id))
        .join(Session, Attendance.session_id == Session.id)
        .where(Session.batch_id == batch_id)
    )

    return {
        "total_students": total_students or 0,
        "total_sessions": total_sessions or 0,
        "total_attendance": total_attendance or 0,
    }


@router.post("/{batch_id}/invite", response_model=BatchInviteRead)
def create_batch_invite(
    batch_id: int,
    db: Annotated[DbSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles("trainer", "institution"))],
) -> BatchInvite:
    batch = db.get(Batch, batch_id)
    if batch is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found",
        )
    if not can_manage_batch(current_user, batch, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User cannot manage this batch",
        )

    invite = BatchInvite(
        batch_id=batch.id,
        invited_by_id=current_user.id,
        token=token_urlsafe(32),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        used=False,
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return invite


@router.post("/join", response_model=BatchJoinRead)
def join_batch(
    payload: BatchJoinRequest,
    db: Annotated[DbSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles("student"))],
) -> BatchJoinRead:
    invite = db.scalar(select(BatchInvite).where(BatchInvite.token == payload.token))
    if invite is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invite not found",
        )
    if invite.used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invite already used",
        )
    expires_at = invite.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invite expired",
        )

    existing_membership = db.get(
        BatchStudent,
        {"batch_id": invite.batch_id, "student_id": current_user.id},
    )
    if existing_membership:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student already joined this batch",
        )

    membership = BatchStudent(batch_id=invite.batch_id, student_id=current_user.id)
    invite.used = True
    db.add(membership)
    db.commit()

    return BatchJoinRead(batch_id=invite.batch_id, student_id=current_user.id)
