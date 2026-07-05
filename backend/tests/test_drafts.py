from __future__ import annotations

from sqlalchemy import select
from fastapi.testclient import TestClient

from backend.app.models.entities import ActionItem, AuditEvent, Draft
from backend.tests.test_auth_and_meetings import _auth_headers, _sign_up


def test_draft_review_queue_supports_edit_approve_and_dismiss(processing_client: TestClient) -> None:
    session = _sign_up(
        processing_client,
        email="draft-owner@example.com",
        name="Draft Owner",
        workspace_name="Draft Workspace",
    )
    headers = _auth_headers(session["access_token"])

    upload_response = processing_client.post(
        "/meetings/upload",
        headers=headers,
        files={"file": ("review.wav", b"fake audio bytes", "audio/wav")},
        data={"title": "Draft Review", "language_hint": "en"},
    )
    assert upload_response.status_code == 201, upload_response.text
    meeting_id = upload_response.json()["id"]

    detail_response = processing_client.get(f"/meetings/{meeting_id}", headers=headers)
    assert detail_response.status_code == 200, detail_response.text
    detail = detail_response.json()
    jira_drafts = [draft for draft in detail["drafts"] if draft["kind"] == "jira_issue"]
    slack_draft = next(draft for draft in detail["drafts"] if draft["kind"] == "slack_message")
    approved_jira_draft = jira_drafts[0]
    dismissed_jira_draft = jira_drafts[1]

    update_response = processing_client.patch(
        f"/meetings/{meeting_id}/drafts/{slack_draft['id']}",
        headers=headers,
        json={
            "payload": {
                "title": "Updated Slack Summary",
                "summary_english": "Updated English summary for the customer channel.",
            }
        },
    )
    assert update_response.status_code == 200, update_response.text
    updated_slack_draft = update_response.json()
    assert updated_slack_draft["payload"]["title"] == "Updated Slack Summary"
    assert updated_slack_draft["payload"]["summary_english"] == "Updated English summary for the customer channel."
    assert updated_slack_draft["status"] == "draft"

    approve_response = processing_client.post(
        f"/meetings/{meeting_id}/drafts/{approved_jira_draft['id']}/approve",
        headers=headers,
    )
    assert approve_response.status_code == 200, approve_response.text
    approved_draft = approve_response.json()
    assert approved_draft["status"] == "approved"
    assert approved_draft["acted_by_user_id"] == session["user"]["id"]
    assert approved_draft["acted_at"] is not None

    dismiss_response = processing_client.post(
        f"/meetings/{meeting_id}/drafts/{dismissed_jira_draft['id']}/dismiss",
        headers=headers,
    )
    assert dismiss_response.status_code == 200, dismiss_response.text
    dismissed_draft = dismiss_response.json()
    assert dismissed_draft["status"] == "dismissed"
    assert dismissed_draft["acted_by_user_id"] == session["user"]["id"]
    assert dismissed_draft["acted_at"] is not None

    list_response = processing_client.get(f"/meetings/{meeting_id}/drafts", headers=headers)
    assert list_response.status_code == 200, list_response.text
    listed_drafts = list_response.json()
    assert len(listed_drafts) == 3
    listed_by_id = {draft["id"]: draft for draft in listed_drafts}
    assert listed_by_id[approved_jira_draft["id"]]["status"] == "approved"
    assert listed_by_id[dismissed_jira_draft["id"]]["status"] == "dismissed"
    assert listed_by_id[slack_draft["id"]]["payload"]["title"] == "Updated Slack Summary"

    final_detail_response = processing_client.get(f"/meetings/{meeting_id}", headers=headers)
    assert final_detail_response.status_code == 200, final_detail_response.text
    final_detail = final_detail_response.json()
    action_items_by_text = {item["text"]: item for item in final_detail["action_items"]}
    assert action_items_by_text["Verify the login fix in staging before the deploy window."]["state"] == "open"
    assert action_items_by_text["Post the client update in Slack after QA passes."]["state"] == "dismissed"

    with processing_client.testing_session_factory() as db:  # type: ignore[attr-defined]
        stored_drafts = list(db.scalars(select(Draft).where(Draft.meeting_id == meeting_id)))
        assert len(stored_drafts) == 3
        assert {draft.status.value for draft in stored_drafts} == {"approved", "dismissed", "draft"}

        dismissed_action_item = db.scalar(
            select(ActionItem).where(ActionItem.text == "Post the client update in Slack after QA passes.")
        )
        assert dismissed_action_item is not None
        assert dismissed_action_item.state.value == "dismissed"

        audit_events = list(db.scalars(select(AuditEvent).where(AuditEvent.target_type == "draft")))
        assert [event.action for event in audit_events] == ["draft.updated", "draft.approved", "draft.dismissed"]


def test_draft_review_queue_stays_workspace_scoped(processing_client: TestClient) -> None:
    owner_session = _sign_up(
        processing_client,
        email="owner-draft@example.com",
        name="Owner Draft",
        workspace_name="Owner Workspace",
    )
    outsider_session = _sign_up(
        processing_client,
        email="outsider-draft@example.com",
        name="Outsider Draft",
        workspace_name="Outsider Workspace",
    )

    upload_response = processing_client.post(
        "/meetings/upload",
        headers=_auth_headers(owner_session["access_token"]),
        files={"file": ("scoped.wav", b"fake audio bytes", "audio/wav")},
        data={"title": "Scoped Draft", "language_hint": "en"},
    )
    assert upload_response.status_code == 201, upload_response.text
    meeting_id = upload_response.json()["id"]

    detail_response = processing_client.get(
        f"/meetings/{meeting_id}",
        headers=_auth_headers(owner_session["access_token"]),
    )
    assert detail_response.status_code == 200, detail_response.text
    draft_id = detail_response.json()["drafts"][0]["id"]

    forbidden_update = processing_client.patch(
        f"/meetings/{meeting_id}/drafts/{draft_id}",
        headers=_auth_headers(outsider_session["access_token"]),
        json={"payload": {"summary": "Should not work"}},
    )
    assert forbidden_update.status_code == 404

    forbidden_approve = processing_client.post(
        f"/meetings/{meeting_id}/drafts/{draft_id}/approve",
        headers=_auth_headers(outsider_session["access_token"]),
    )
    assert forbidden_approve.status_code == 404
