from typing import Annotated

from fastapi import APIRouter, Depends

from app.schemas import MonitoringTokenRequest, TokenResponse
from app.security import create_monitoring_token, get_monitoring_token_payload


router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.post("/token", response_model=TokenResponse)
def issue_monitoring_token(payload: MonitoringTokenRequest) -> TokenResponse:
    return TokenResponse(access_token=create_monitoring_token(payload.api_key))


@router.get("/health")
def monitoring_health(
    token_payload: Annotated[dict, Depends(get_monitoring_token_payload)],
) -> dict[str, str]:
    return {"status": "ok", "role": token_payload["role"]}
