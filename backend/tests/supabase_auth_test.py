import getpass

import requests

from app.core.config import settings


def main() -> None:
    """Manually check Supabase login and the protected API route."""
    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        raise RuntimeError("Supabase URL or anon key is missing from .env")
    if not settings.API_BASE_URL:
        raise RuntimeError("API_BASE_URL is missing from .env")

    email = input("Enter test user email: ")
    password = getpass.getpass("Enter test user password: ")

    response = requests.post(
        f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/token?grant_type=password",
        headers={
            "apikey": settings.SUPABASE_ANON_KEY,
            "Content-Type": "application/json",
        },
        json={"email": email, "password": password},
        timeout=20,
    )

    if response.status_code != 200:
        print("Authentication failed.")
        print("Status:", response.status_code)
        print("Response:", response.json())
        raise SystemExit(1)

    access_token = response.json()["access_token"]
    print("\nSupabase login successful!")
    print("Access token obtained (not displayed).")

    api_response = requests.get(
        f"{settings.API_BASE_URL.rstrip('/')}{settings.API_V1_PREFIX}/auth-check",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=20,
    )
    print("\nBackend authentication test:")
    print("Status:", api_response.status_code)
    print("Response:", api_response.json())


if __name__ == "__main__":
    main()
