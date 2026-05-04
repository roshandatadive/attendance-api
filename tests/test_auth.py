from fastapi.testclient import TestClient


def test_signup_and_login(client: TestClient) -> None:
    signup_response = client.post(
        "/auth/signup",
        json={
            "name": "Student One",
            "email": "student@example.com",
            "password": "secret123",
        },
    )

    assert signup_response.status_code == 201
    assert signup_response.json()["email"] == "student@example.com"
    assert signup_response.json()["role"] == "student"
    assert "password" not in signup_response.json()

    login_response = client.post(
        "/auth/login",
        json={"email": "student@example.com", "password": "secret123"},
    )

    assert login_response.status_code == 200
    assert login_response.json()["token_type"] == "bearer"
    assert login_response.json()["access_token"]


def test_no_token_returns_401(client: TestClient) -> None:
    response = client.post(
        "/sessions",
        json={"batch_id": 1, "session_date": "2026-05-03"},
    )

    assert response.status_code == 401
    assert response.json()["error"] == "Unauthorized"
