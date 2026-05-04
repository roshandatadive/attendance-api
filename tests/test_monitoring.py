from fastapi.testclient import TestClient


def test_monitoring_post_to_get_route_returns_405(client: TestClient) -> None:
    token_response = client.post(
        "/monitoring/token",
        json={"api_key": "test-monitoring-key"},
    )
    token = token_response.json()["access_token"]

    response = client.post(
        "/monitoring/health",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 405
