from fastapi import APIRouter

from app.core.responses import success_response

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check() -> dict[str, object]:
    return success_response("Career Compass API is healthy")