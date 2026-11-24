from typing import Any


def success_response(message: str, data: Any | None = None) -> dict[str, Any]:
    """Build the standard successful API response envelope."""
    return {"success": True, "message": message, "data": {} if data is None else data}