from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient


def _sign_up(
    client: TestClient,
    *,
    email: str,
    name: str,
    password: str = "pass12345",
    workspace_name: str,
) -> dict[str, object]:
    response = client.post(
        "/auth/sign-up",
        json={
            "email": email,
            "name": name,
            "password": password,
            "workspace_name": workspace_name,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def test_invite_acceptance_and_session_flow(client: TestClient) -> None:
    owner_session = _sign_up(
        client,
        email="owner@example.com",
        name="Owner",
        workspace_name="Workspace A",
    )
    owner_headers = _auth_headers(owner_session["access_token"])

    invite_response = client.post(
        "/auth/invites",
        headers=owner_headers,
        json={"email": "member@example.com"},
    )
    assert invite_response.status_code == 201, invite_response.text
    invite = invite_response.json()
    assert invite["status"] == "pending"

    accept_response = client.post(
        "/auth/invites/accept",
        json={
            "token": invite["token"],
            "email": "member@example.com",
            "name": "Member",
            "password": "pass12345",
        },
    )
    assert accept_response.status_code == 201, accept_response.text
    member_session = accept_response.json()
    assert member_session["user"]["role"] == "member"
    assert member_session["workspace"]["id"] == owner_session["workspace"]["id"]

    session_response = client.get("/auth/session", headers=_auth_headers(member_session["access_token"]))
    assert session_response.status_code == 200, session_response.text
    assert session_response.json()["user"]["email"] == "member@example.com"


def test_cors_preflight_allows_local_frontend_origin(client: TestClient) -> None:
    response = client.options(
        "/health",
        headers={
            "Origin": "http://127.0.0.1:3001",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200, response.text
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:3001"


def test_meeting_upload_list_detail_delete_and_workspace_boundary(client: TestClient) -> None:
    first_user = _sign_up(
        client,
        email="alice@example.com",
        name="Alice",
        workspace_name="Workspace A",
    )
    second_user = _sign_up(
        client,
        email="bob@example.com",
        name="Bob",
        workspace_name="Workspace B",
    )

    upload_response = client.post(
        "/meetings/upload",
        headers=_auth_headers(first_user["access_token"]),
        files={"file": ("daily-standup.wav", b"fake audio bytes", "audio/wav")},
        data={"title": "Daily Standup", "language_hint": "en"},
    )
    assert upload_response.status_code == 201, upload_response.text
    meeting = upload_response.json()
    assert meeting["status"] == "uploaded"
    assert client.recording_orchestrator.enqueued_meeting_ids == [meeting["id"]]  # type: ignore[attr-defined]

    stored_path = client.storage_service.resolve_relative_path(meeting["audio_object_key"])  # type: ignore[attr-defined]
    assert stored_path.exists()

    audio_response = client.get(f"/meetings/{meeting['id']}/audio", headers=_auth_headers(first_user["access_token"]))
    assert audio_response.status_code == 200, audio_response.text
    assert audio_response.content == b"fake audio bytes"
    assert audio_response.headers["content-type"].startswith("audio/")

    first_list = client.get("/meetings", headers=_auth_headers(first_user["access_token"]))
    assert first_list.status_code == 200, first_list.text
    assert first_list.json()["total"] == 1
    assert first_list.json()["items"][0]["id"] == meeting["id"]

    second_list = client.get("/meetings", headers=_auth_headers(second_user["access_token"]))
    assert second_list.status_code == 200, second_list.text
    assert second_list.json() == {"items": [], "total": 0}

    detail_response = client.get(f"/meetings/{meeting['id']}", headers=_auth_headers(first_user["access_token"]))
    assert detail_response.status_code == 200, detail_response.text
    detail = detail_response.json()
    assert detail["id"] == meeting["id"]
    assert detail["transcript_segments"] == []
    assert detail["action_items"] == []
    assert detail["drafts"] == []
    assert detail["analysis"] is None

    forbidden_detail = client.get(f"/meetings/{meeting['id']}", headers=_auth_headers(second_user["access_token"]))
    assert forbidden_detail.status_code == 404

    reprocess_response = client.post(
        f"/meetings/{meeting['id']}/reprocess",
        headers=_auth_headers(first_user["access_token"]),
    )
    assert reprocess_response.status_code == 202, reprocess_response.text
    assert client.recording_orchestrator.enqueued_meeting_ids == [meeting["id"], meeting["id"]]  # type: ignore[attr-defined]

    delete_response = client.delete(f"/meetings/{meeting['id']}", headers=_auth_headers(first_user["access_token"]))
    assert delete_response.status_code == 204, delete_response.text
    assert not stored_path.exists()

    missing_after_delete = client.get(f"/meetings/{meeting['id']}", headers=_auth_headers(first_user["access_token"]))
    assert missing_after_delete.status_code == 404


def test_workspace_settings_allow_owner_update_and_member_read(client: TestClient) -> None:
    owner_session = _sign_up(
        client,
        email="settings-owner@example.com",
        name="Settings Owner",
        workspace_name="Settings Workspace",
    )
    owner_headers = _auth_headers(owner_session["access_token"])

    invite_response = client.post(
        "/auth/invites",
        headers=owner_headers,
        json={"email": "settings-member@example.com"},
    )
    assert invite_response.status_code == 201, invite_response.text
    invite = invite_response.json()

    member_response = client.post(
        "/auth/invites/accept",
        json={
            "token": invite["token"],
            "email": "settings-member@example.com",
            "name": "Settings Member",
            "password": "pass12345",
        },
    )
    assert member_response.status_code == 201, member_response.text
    member_session = member_response.json()

    initial_settings_response = client.get("/workspace/settings", headers=owner_headers)
    assert initial_settings_response.status_code == 200, initial_settings_response.text
    initial_body = initial_settings_response.json()
    assert initial_body["workspace"]["settings"]["default_language_hint"] == "auto"
    assert initial_body["workspace"]["settings"]["slack_channel"] == ""
    assert initial_body["workspace"]["settings"]["slack_auto_post"] is False
    assert {item["provider"] for item in initial_body["integrations"]} == {"google", "slack", "jira"}
    assert all(item["connected"] is False for item in initial_body["integrations"])

    member_update_response = client.patch(
        "/workspace/settings",
        headers=_auth_headers(member_session["access_token"]),
        json={
            "default_language_hint": "si",
            "slack_channel": "#delivery",
            "slack_auto_post": True,
        },
    )
    assert member_update_response.status_code == 403

    owner_update_response = client.patch(
        "/workspace/settings",
        headers=owner_headers,
        json={
            "default_language_hint": "si",
            "slack_channel": "#delivery",
            "slack_auto_post": True,
        },
    )
    assert owner_update_response.status_code == 200, owner_update_response.text
    updated_body = owner_update_response.json()
    assert updated_body["workspace"]["settings"]["default_language_hint"] == "si"
    assert updated_body["workspace"]["settings"]["slack_channel"] == "#delivery"
    assert updated_body["workspace"]["settings"]["slack_auto_post"] is True

    member_settings_response = client.get(
        "/workspace/settings",
        headers=_auth_headers(member_session["access_token"]),
    )
    assert member_settings_response.status_code == 200, member_settings_response.text
    member_body = member_settings_response.json()
    assert member_body["workspace"]["settings"]["default_language_hint"] == "si"
    assert member_body["workspace"]["settings"]["slack_channel"] == "#delivery"
    assert member_body["workspace"]["settings"]["slack_auto_post"] is True
