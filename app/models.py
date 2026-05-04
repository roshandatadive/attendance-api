from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class BatchTrainer(Base):
    __tablename__ = "batch_trainers"

    batch_id: Mapped[int] = mapped_column(ForeignKey("batches.id"), primary_key=True)
    trainer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)

    batch: Mapped["Batch"] = relationship(back_populates="batch_trainers")
    trainer: Mapped["User"] = relationship(back_populates="trainer_batches")


class BatchStudent(Base):
    __tablename__ = "batch_students"

    batch_id: Mapped[int] = mapped_column(ForeignKey("batches.id"), primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)

    batch: Mapped["Batch"] = relationship(back_populates="batch_students")
    student: Mapped["User"] = relationship(back_populates="student_batches")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50))

    trainer_batches: Mapped[list[BatchTrainer]] = relationship(back_populates="trainer")
    student_batches: Mapped[list[BatchStudent]] = relationship(back_populates="student")
    sent_invites: Mapped[list["BatchInvite"]] = relationship(back_populates="invited_by")
    attendance_records: Mapped[list["Attendance"]] = relationship(back_populates="student")


class Batch(Base):
    __tablename__ = "batches"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    institution_id: Mapped[int | None] = mapped_column(nullable=True)
    programme_id: Mapped[int | None] = mapped_column(nullable=True)

    batch_trainers: Mapped[list[BatchTrainer]] = relationship(back_populates="batch")
    batch_students: Mapped[list[BatchStudent]] = relationship(back_populates="batch")
    invites: Mapped[list["BatchInvite"]] = relationship(back_populates="batch")
    sessions: Mapped[list["Session"]] = relationship(back_populates="batch")


class BatchInvite(Base):
    __tablename__ = "batch_invites"

    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("batches.id"))
    invited_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    token: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    used: Mapped[bool] = mapped_column(Boolean, default=False)

    batch: Mapped[Batch] = relationship(back_populates="invites")
    invited_by: Mapped[User] = relationship(back_populates="sent_invites")


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("batches.id"))
    session_date: Mapped[date] = mapped_column(Date)

    batch: Mapped[Batch] = relationship(back_populates="sessions")
    attendance_records: Mapped[list["Attendance"]] = relationship(back_populates="session")


class Attendance(Base):
    __tablename__ = "attendance"
    __table_args__ = (
        UniqueConstraint("session_id", "student_id", name="uq_attendance_session_student"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"))
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String(50))
    marked_at: Mapped[datetime] = mapped_column(DateTime)

    session: Mapped[Session] = relationship(back_populates="attendance_records")
    student: Mapped[User] = relationship(back_populates="attendance_records")
