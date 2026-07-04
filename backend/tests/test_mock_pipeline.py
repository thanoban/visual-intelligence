from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.models.entities import JobStage
from backend.tests.test_auth_and_meetings import _auth_headers, _sign_up


def test_upload_runs_mock_pipeline_to_completion(processing_client: TestClient) -> None:
    session = _sign_up(
        processing_client,
        email="pipeline@example.com",
        name="Pipeline User",
        workspace_name="Pipeline Workspace",
    )

    upload_response = processing_client.post(
        "/meetings/upload",
        headers=_auth_headers(session["access_token"]),
        files={"file": ("sync.wav", b"fake audio bytes", "audio/wav")},
        data={"title": "Sprint Sync", "language_hint": "en"},
    )
    assert upload_response.status_code == 201, upload_response.text
    upload_body = upload_response.json()
    assert upload_body["status"] == "uploaded"

    detail_response = processing_client.get(
        f"/meetings/{upload_body['id']}",
        headers=_auth_headers(session["access_token"]),
    )
    assert detail_response.status_code == 200, detail_response.text
    detail = detail_response.json()
    assert detail["status"] == "completed"
    assert len(detail["transcript_segments"]) == 3
    assert detail["analysis"]["summary_english"]
    assert len(detail["action_items"]) == 2
    assert len(detail["drafts"]) == 3
    assert {draft["kind"] for draft in detail["drafts"]} == {"jira_issue", "slack_message"}


def test_failed_stage_can_be_reprocessed_from_failure_point(processing_client: TestClient) -> None:
    session = _sign_up(
        processing_client,
        email="retry@example.com",
        name="Retry User",
        workspace_name="Retry Workspace",
    )

    upload_response = processing_client.post(
        "/meetings/upload",
        headers=_auth_headers(session["access_token"]),
        files={"file": ("retry.wav", b"fake audio bytes", "audio/wav")},
        data={"title": "Release Review", "language_hint": "en"},
    )
    assert upload_response.status_code == 201, upload_response.text
    meeting_id = upload_response.json()["id"]

    processing_client.failure_injector.schedule_failure(meeting_id, JobStage.ANALYZE, times=2)  # type: ignore[attr-defined]
    reprocess_failure = processing_client.post(
        f"/meetings/{meeting_id}/reprocess",
        headers=_auth_headers(session["access_token"]),
    )
    assert reprocess_failure.status_code == 202, reprocess_failure.text

    failed_detail = processing_client.get(
        f"/meetings/{meeting_id}",
        headers=_auth_headers(session["access_token"]),
    )
    assert failed_detail.status_code == 200, failed_detail.text
    failed_body = failed_detail.json()
    assert failed_body["status"] == "failed"
    assert failed_body["error_reason"] == "analyze failed: Forced failure at analyze stage"
    assert len(failed_body["transcript_segments"]) == 3
    assert failed_body["analysis"] is None

    reprocess_success = processing_client.post(
        f"/meetings/{meeting_id}/reprocess",
        headers=_auth_headers(session["access_token"]),
    )
    assert reprocess_success.status_code == 202, reprocess_success.text

    final_detail = processing_client.get(
        f"/meetings/{meeting_id}",
        headers=_auth_headers(session["access_token"]),
    )
    assert final_detail.status_code == 200, final_detail.text
    final_body = final_detail.json()
    assert final_body["status"] == "completed"
    assert len(final_body["action_items"]) == 2
    assert len(final_body["drafts"]) == 3
