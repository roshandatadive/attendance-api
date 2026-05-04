from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Batch, BatchStudent, BatchTrainer, Session as ClassSession, User
from app.security import hash_password


def create_user(db_session: Session, email: str, password: str, role: str) -> User:
    user = User(
        name=role.title(),
        email=email,
        password_hash=hash_password(password),
        role=role,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def auth_headers(
    client: TestClient,
    db_session: Session,
    email: str,
    password: str,
    role: str,
) -> dict[str, str]:
    create_user(db_session, email, password, role)
    login_response = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_trainer_can_create_session(client: TestClient, db_session: Session) -> None:
    batch = Batch(name="Backend Batch")
    db_session.add(batch)
    db_session.commit()
    db_session.refresh(batch)

    trainer = create_user(db_session, "trainer@example.com", "secret123", "trainer")
    db_session.add(BatchTrainer(batch_id=batch.id, trainer_id=trainer.id))
    db_session.commit()

    login_response = client.post(
        "/auth/login",
        json={"email": "trainer@example.com", "password": "secret123"},
    )
    headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}
    response = client.post(
        "/sessions",
        json={"batch_id": batch.id, "session_date": "2026-05-03"},
        headers=headers,
    )

    assert response.status_code == 201
    assert response.json()["batch_id"] == batch.id
    assert response.json()["session_date"] == "2026-05-03"


def test_student_can_mark_attendance(client: TestClient, db_session: Session) -> None:
    batch = Batch(name="Backend Batch")
    db_session.add(batch)
    db_session.commit()
    db_session.refresh(batch)

    session = ClassSession(batch_id=batch.id, session_date=date(2026, 5, 3))
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)

    student = create_user(db_session, "student@example.com", "secret123", "student")
    db_session.add(BatchStudent(batch_id=batch.id, student_id=student.id))
    db_session.commit()

    login_response = client.post(
        "/auth/login",
        json={"email": "student@example.com", "password": "secret123"},
    )
    headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}
    response = client.post(
        "/attendance",
        json={"session_id": session.id, "status": "present"},
        headers=headers,
    )

    assert response.status_code == 201
    assert response.json()["session_id"] == session.id
    assert response.json()["status"] == "present"
