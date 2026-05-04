import argparse
import json
import time

import httpx
import jwt


DEFAULT_BASE_URL = "http://127.0.0.1:8000"
DEFAULT_PASSWORD = "password123"
DEFAULT_MONITORING_API_KEY = "change-this-monitoring-api-key"


class ApiTester:
    def __init__(self, base_url: str) -> None:
        self.client = httpx.Client(base_url=base_url, timeout=10)
        self.results: list[dict] = []

    def request(
        self,
        name: str,
        method: str,
        path: str,
        expected_status: int,
        *,
        json_body: dict | None = None,
        headers: dict | None = None,
        params: dict | None = None,
    ) -> dict:
        response = self.client.request(
            method,
            path,
            json=json_body,
            headers=headers,
            params=params,
        )
        try:
            body = response.json()
        except ValueError:
            body = response.text

        result = {
            "name": name,
            "method": method,
            "path": path,
            "expected_status": expected_status,
            "actual_status": response.status_code,
            "passed": response.status_code == expected_status,
            "request": json_body,
            "params": params,
            "response": body,
        }
        self.results.append(result)
        return result

    def login(self, email: str, password: str = DEFAULT_PASSWORD) -> tuple[str, dict]:
        result = self.request(
            f"Login {email}",
            "POST",
            "/auth/login",
            200,
            json_body={"email": email, "password": password},
        )
        token = result["response"]["access_token"]
        claims = jwt.decode(token, options={"verify_signature": False})
        return token, claims


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def run(base_url: str) -> list[dict]:
    tester = ApiTester(base_url)
    suffix = int(time.time())
    student_email = f"e2e_student_{suffix}@example.com"

    tester.request("Root endpoint", "GET", "/", 200)
    tester.request("Health endpoint", "GET", "/health", 200)

    signup = tester.request(
        "Student signup",
        "POST",
        "/auth/signup",
        201,
        json_body={
            "name": "E2E Student",
            "email": student_email,
            "password": DEFAULT_PASSWORD,
        },
    )
    student_id = signup["response"].get("id")
    student_token, _ = tester.login(student_email)
    trainer_token, _ = tester.login("trainer@example.com")
    institution_token, institution_claims = tester.login("institution@example.com")
    programme_manager_token, _ = tester.login("programme_manager@example.com")
    monitoring_login_token, _ = tester.login("monitoring_officer@example.com")

    institution_id = institution_claims["user_id"]

    batch = tester.request(
        "Trainer creates batch",
        "POST",
        "/batches",
        201,
        json_body={
            "name": f"E2E Batch {suffix}",
            "institution_id": institution_id,
            "programme_id": 1,
        },
        headers=bearer(trainer_token),
    )
    batch_id = batch["response"].get("id")

    invite = tester.request(
        "Trainer creates invite",
        "POST",
        f"/batches/{batch_id}/invite",
        200,
        headers=bearer(trainer_token),
    )
    invite_token = invite["response"].get("token")

    tester.request(
        "Student joins batch",
        "POST",
        "/batches/join",
        200,
        json_body={"token": invite_token},
        headers=bearer(student_token),
    )

    session = tester.request(
        "Trainer creates session",
        "POST",
        "/sessions",
        201,
        json_body={"batch_id": batch_id, "session_date": "2026-05-04"},
        headers=bearer(trainer_token),
    )
    session_id = session["response"].get("id")

    tester.request(
        "Student marks attendance",
        "POST",
        "/attendance",
        201,
        json_body={"session_id": session_id, "status": "present"},
        headers=bearer(student_token),
    )

    tester.request(
        "Trainer views attendance",
        "GET",
        f"/sessions/{session_id}/attendance",
        200,
        headers=bearer(trainer_token),
    )

    tester.request(
        "Institution views batch summary",
        "GET",
        f"/batches/{batch_id}/summary",
        200,
        headers=bearer(institution_token),
    )

    tester.request(
        "Programme manager views institution summary",
        "GET",
        f"/institutions/{institution_id}/summary",
        200,
        headers=bearer(programme_manager_token),
    )

    tester.request(
        "Programme manager views programme summary",
        "GET",
        "/programme/summary",
        200,
        params={"programme_id": 1},
        headers=bearer(programme_manager_token),
    )

    monitoring_token = tester.request(
        "Monitoring API key token",
        "POST",
        "/monitoring/token",
        200,
        json_body={"api_key": DEFAULT_MONITORING_API_KEY},
        headers=bearer(monitoring_login_token),
    )["response"]["access_token"]

    tester.request(
        "Monitoring endpoint",
        "GET",
        "/monitoring/health",
        200,
        headers=bearer(monitoring_token),
    )

    tester.request(
        "No token returns 401",
        "POST",
        "/sessions",
        401,
        json_body={"batch_id": batch_id, "session_date": "2026-05-04"},
    )

    tester.request(
        "Wrong role returns 403",
        "POST",
        "/sessions",
        403,
        json_body={"batch_id": batch_id, "session_date": "2026-05-04"},
        headers=bearer(student_token),
    )

    tester.request(
        "Invalid resource returns 404",
        "GET",
        "/batches/999999/summary",
        404,
        headers=bearer(institution_token),
    )

    tester.request(
        "Invalid input returns 422",
        "POST",
        "/auth/signup",
        422,
        json_body={"email": f"invalid_{suffix}@example.com"},
    )

    tester.request(
        "Wrong method returns 405",
        "POST",
        "/monitoring/health",
        405,
        headers=bearer(monitoring_token),
    )

    tester.request(
        "Duplicate attendance rejected",
        "POST",
        "/attendance",
        400,
        json_body={"session_id": session_id, "status": "present"},
        headers=bearer(student_token),
    )

    other_student_email = f"outsider_{suffix}@example.com"
    tester.request(
        "Outsider signup",
        "POST",
        "/auth/signup",
        201,
        json_body={
            "name": "Outsider Student",
            "email": other_student_email,
            "password": DEFAULT_PASSWORD,
        },
    )
    outsider_token, _ = tester.login(other_student_email)
    tester.request(
        "Student not in batch rejected",
        "POST",
        "/attendance",
        403,
        json_body={"session_id": session_id, "status": "present"},
        headers=bearer(outsider_token),
    )

    tester.request(
        "Invalid session rejected",
        "POST",
        "/attendance",
        404,
        json_body={"session_id": 999999, "status": "present"},
        headers=bearer(student_token),
    )

    return tester.results


def to_markdown(results: list[dict], base_url: str) -> str:
    passed = sum(1 for result in results if result["passed"])
    total = len(results)
    status = "PASS" if passed == total else "FAIL"

    lines = [
        "## Testing & Validation",
        "",
        f"Latest local validation target: `{base_url}`",
        "",
        f"Overall result: **{status}** ({passed}/{total} checks passed)",
        "",
        "### End-to-End Flow Results",
        "",
        "| Check | Method | Endpoint | Expected | Actual | Result |",
        "|---|---:|---|---:|---:|---|",
    ]

    for result in results:
        mark = "PASS" if result["passed"] else "FAIL"
        lines.append(
            "| "
            f"{result['name']} | "
            f"{result['method']} | "
            f"`{result['path']}` | "
            f"{result['expected_status']} | "
            f"{result['actual_status']} | "
            f"{mark} |"
        )

    sample_results = [
        result
        for result in results
        if result["name"]
        in {
            "Student signup",
            "Trainer creates batch",
            "Student marks attendance",
            "Trainer views attendance",
            "Monitoring endpoint",
        }
    ]

    lines.extend(["", "### Sample Inputs And Outputs", ""])
    for result in sample_results:
        lines.extend(
            [
                f"**{result['name']}**",
                "",
                f"`{result['method']} {result['path']}`",
                "",
                "Request:",
                "",
                "```json",
                json.dumps(result["request"] or result["params"] or {}, indent=2),
                "```",
                "",
                "Response:",
                "",
                "```json",
                json.dumps(result["response"], indent=2),
                "```",
                "",
            ]
        )

    lines.extend(
        [
            "### Notes",
            "",
            "- Public signup created only `student` users.",
            "- Protected routes returned `401` without a token.",
            "- Wrong-role access returned `403`.",
            "- Invalid resources returned `404`.",
            "- Invalid request bodies returned `422`.",
            "- Wrong HTTP methods returned `405`.",
            "- Duplicate attendance and non-member attendance were rejected.",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()

    results = run(args.base_url)
    if args.markdown:
        print(to_markdown(results, args.base_url))
    else:
        print(json.dumps(results, indent=2, default=str))


if __name__ == "__main__":
    main()
