import time

import requests


BASE_URL = "http://127.0.0.1:8000"
PASSWORD = "password123"


def log(name: str, success: bool, status_code: int, body: object = "") -> None:
    status = "PASS" if success else "FAIL"
    print(f"{name}: {status} ({status_code})")
    if not success:
        print(body)


def login(email: str) -> str:
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": email, "password": PASSWORD},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def main() -> None:
    email = f"smoke_student_{int(time.time())}@test.com"

    response = requests.post(
        f"{BASE_URL}/auth/signup",
        json={
            "name": "Smoke Student",
            "email": email,
            "password": PASSWORD,
        },
        timeout=10,
    )
    log("Signup creates student", response.status_code == 201, response.status_code, response.text)

    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": email, "password": PASSWORD},
        timeout=10,
    )
    student_token = response.json().get("access_token", "")
    log("Student login", response.status_code == 200 and bool(student_token), response.status_code, response.text)

    student_headers = {"Authorization": f"Bearer {student_token}"}

    response = requests.post(
        f"{BASE_URL}/sessions",
        json={"batch_id": 1, "session_date": "2026-05-05"},
        headers=student_headers,
        timeout=10,
    )
    log("Student create session rejected", response.status_code == 403, response.status_code, response.text)

    response = requests.post(
        f"{BASE_URL}/sessions",
        json={"batch_id": 1, "session_date": "2026-05-05"},
        timeout=10,
    )
    log("No token rejected", response.status_code == 401, response.status_code, response.text)

    institution_token = login("institution@example.com")
    institution_headers = {"Authorization": f"Bearer {institution_token}"}
    response = requests.get(
        f"{BASE_URL}/batches/999999/summary",
        headers=institution_headers,
        timeout=10,
    )
    log("Invalid batch returns 404", response.status_code == 404, response.status_code, response.text)

    response = requests.post(
        f"{BASE_URL}/auth/signup",
        json={"email": f"invalid_{int(time.time())}@test.com"},
        timeout=10,
    )
    log("Invalid input returns 422", response.status_code == 422, response.status_code, response.text)

    monitoring_response = requests.post(
        f"{BASE_URL}/monitoring/token",
        json={"api_key": "change-this-monitoring-api-key"},
        timeout=10,
    )
    monitoring_token = monitoring_response.json().get("access_token", "")
    log(
        "Monitoring token issued",
        monitoring_response.status_code == 200 and bool(monitoring_token),
        monitoring_response.status_code,
        monitoring_response.text,
    )

    response = requests.post(
        f"{BASE_URL}/monitoring/health",
        headers={"Authorization": f"Bearer {monitoring_token}"},
        timeout=10,
    )
    log("Wrong method returns 405", response.status_code == 405, response.status_code, response.text)

    print("\nSmoke test completed")


if __name__ == "__main__":
    main()
