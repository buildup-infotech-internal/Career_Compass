from collections.abc import Iterator
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.main import app
from app.models.user import Profile

AUTHENTICATED_USER_ID = UUID("6f1c12fd-1ed6-4f85-87dc-438a8545ec34")
OTHER_USER_ID = UUID("e3e55b3d-a8d2-42d2-b30c-7f26e25d0f9f")


class FakeProfileSession:
    def __init__(self) -> None:
        self.profiles: dict[UUID, Profile] = {}
        self.deleted_ids: list[UUID] = []
        self.commits = 0
        self.rollbacks = 0
        self.fail_commit = False

    def scalar(self, statement: object) -> Profile | None:
        query_params = statement.compile().params  # type: ignore[attr-defined]
        queried_user_id = next(iter(query_params.values()))
        return self.profiles.get(queried_user_id)

    def add(self, profile: Profile) -> None:
        self.profiles[profile.id] = profile

    def commit(self) -> None:
        if self.fail_commit:
            raise SQLAlchemyError("simulated database failure")
        self.commits += 1

    def refresh(self, _: Profile) -> None:
        pass

    def delete(self, profile: Profile) -> None:
        self.deleted_ids.append(profile.id)
        self.profiles.pop(profile.id, None)

    def rollback(self) -> None:
        self.rollbacks += 1


@pytest.fixture

def profile_client() -> Iterator[tuple[TestClient, FakeProfileSession]]:
    session = FakeProfileSession()
    app.dependency_overrides[get_current_user] = lambda: AUTHENTICATED_USER_ID

    def override_db() -> Iterator[FakeProfileSession]:
        yield session

    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as client:
            yield client, session
    finally:
        app.dependency_overrides.clear()


def test_profile_routes_require_authentication() -> None:
    with TestClient(app) as client:
        responses = [
            client.get("/api/v1/profiles/me"),
            client.put("/api/v1/profiles/me", json={"full_name": "Jordan Lee"}),
            client.delete("/api/v1/profiles/me"),
        ]

    for response in responses:
        assert response.status_code == 401
        assert response.json()["success"] is False


def test_get_returns_only_authenticated_users_profile(
    profile_client: tuple[TestClient, FakeProfileSession],
) -> None:
    client, session = profile_client
    session.profiles[AUTHENTICATED_USER_ID] = Profile(
        id=AUTHENTICATED_USER_ID,
        full_name="Jordan Lee",
        phone="+1 202 555 0144",
        location="Toronto",
        education=[{"degree": "BSc", "institution": "Example University", "year": 2024}],
        experience=[],
        account_role="learner",
    )

    response = client.get("/api/v1/profiles/me")

    assert response.status_code == 200
    assert response.json()["data"] == {
        "id": str(AUTHENTICATED_USER_ID),
        "full_name": "Jordan Lee",
        "phone": "+1 202 555 0144",
        "location": "Toronto",
        "education": [
            {"degree": "BSc", "institution": "Example University", "year": 2024}
        ],
        "experience": [],
        "account_role": "learner",
    }


def test_missing_profile_returns_404(
    profile_client: tuple[TestClient, FakeProfileSession],
) -> None:
    client, _ = profile_client

    response = client.get("/api/v1/profiles/me")

    assert response.status_code == 404
    assert response.json()["message"] == "Profile not found"


def test_put_creates_profile_using_authenticated_user_id(
    profile_client: tuple[TestClient, FakeProfileSession],
) -> None:
    client, session = profile_client
    payload = {
        "full_name": "Jordan Lee",
        "phone": "+1 (202) 555-0144",
        "location": "Toronto, Canada",
        "education": [
            {"degree": "BSc", "institution": "Example University", "year": 2024}
        ],
        "experience": [
            {
                "company": "Example Co.",
                "role": "Analyst Intern",
                "duration_months": 6,
                "description": "Built reports",
            }
        ],
    }

    response = client.put("/api/v1/profiles/me", json=payload)

    assert response.status_code == 200
    assert response.json()["data"]["id"] == str(AUTHENTICATED_USER_ID)
    assert response.json()["data"]["account_role"] == "learner"
    assert session.profiles[AUTHENTICATED_USER_ID].education[0]["degree"] == "BSc"
    assert session.commits == 1


def test_put_updates_profile_without_changing_existing_admin_role(
    profile_client: tuple[TestClient, FakeProfileSession],
) -> None:
    client, session = profile_client
    session.profiles[AUTHENTICATED_USER_ID] = Profile(
        id=AUTHENTICATED_USER_ID,
        full_name="Administrator",
        account_role="admin",
    )

    response = client.put(
        "/api/v1/profiles/me",
        json={"full_name": "Updated Name"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["full_name"] == "Updated Name"
    assert response.json()["data"]["account_role"] == "admin"


def test_client_cannot_set_role_or_profile_id(
    profile_client: tuple[TestClient, FakeProfileSession],
) -> None:
    client, session = profile_client

    response = client.put(
        "/api/v1/profiles/me",
        json={"id": str(OTHER_USER_ID), "account_role": "admin"},
    )

    assert response.status_code == 422
    assert response.json()["success"] is False
    assert session.profiles == {}
    assert session.commits == 0


def test_other_users_profile_cannot_be_read_updated_or_deleted(
    profile_client: tuple[TestClient, FakeProfileSession],
) -> None:
    client, session = profile_client
    other_profile = Profile(
        id=OTHER_USER_ID,
        full_name="Other User",
        account_role="learner",
    )
    session.profiles[OTHER_USER_ID] = other_profile

    get_response = client.get("/api/v1/profiles/me")
    delete_response = client.delete("/api/v1/profiles/me")
    update_response = client.put(
        "/api/v1/profiles/me",
        json={"full_name": "Attacker"},
    )

    assert get_response.status_code == 404
    assert delete_response.status_code == 404
    assert update_response.status_code == 200
    assert session.profiles[OTHER_USER_ID] is other_profile
    assert other_profile.full_name == "Other User"
    assert session.deleted_ids == []


def test_delete_removes_only_application_profile(
    profile_client: tuple[TestClient, FakeProfileSession],
) -> None:
    client, session = profile_client
    profile = Profile(
        id=AUTHENTICATED_USER_ID,
        full_name="Jordan Lee",
        account_role="learner",
    )
    session.profiles[AUTHENTICATED_USER_ID] = profile

    response = client.delete("/api/v1/profiles/me")

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert session.deleted_ids == [AUTHENTICATED_USER_ID]
    assert AUTHENTICATED_USER_ID not in session.profiles


def test_invalid_profile_data_returns_422(
    profile_client: tuple[TestClient, FakeProfileSession],
) -> None:
    client, session = profile_client

    response = client.put(
        "/api/v1/profiles/me",
        json={"phone": "not a phone", "location": "   "},
    )

    assert response.status_code == 422
    assert response.json()["success"] is False
    assert session.commits == 0


def test_database_write_error_rolls_back_and_returns_generic_500(
    profile_client: tuple[TestClient, FakeProfileSession],
) -> None:
    client, session = profile_client
    session.fail_commit = True

    response = client.put(
        "/api/v1/profiles/me",
        json={"full_name": "Jordan Lee"},
    )

    assert response.status_code == 500
    assert response.json()["success"] is False
    assert "simulated database failure" not in response.text
    assert session.rollbacks == 1
