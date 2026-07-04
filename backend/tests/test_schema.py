from sqlalchemy import create_engine, inspect

from backend.app.db import Base
from backend.app.models import entities as _entities  # noqa: F401


def test_schema_creates_expected_tables() -> None:
    engine = create_engine("sqlite:///:memory:")

    Base.metadata.create_all(bind=engine)

    tables = set(inspect(engine).get_table_names())

    assert tables == {
        "action_items",
        "audit_events",
        "drafts",
        "integration_connections",
        "job_runs",
        "meeting_analyses",
        "meetings",
        "transcript_segments",
        "users",
        "workspace_invites",
        "workspaces",
    }
