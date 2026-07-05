"use client";

import { Check, LoaderCircle, PencilLine, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { approveDraft, dismissDraft, updateDraft } from "@/lib/api";
import { formatDateTime } from "@/lib/format";
import type { DraftResponse } from "@/lib/types";

import { StatusBadge } from "./status-badge";

interface DraftQueueProps {
  accessToken: string;
  meetingId: string;
  drafts: DraftResponse[];
  onRefresh: () => Promise<void>;
}

interface DraftEditorState {
  title: string;
  summary: string;
  description: string;
  summaryEnglish: string;
}

function getEditorState(draft: DraftResponse): DraftEditorState {
  return {
    title: typeof draft.payload.title === "string" ? draft.payload.title : "",
    summary: typeof draft.payload.summary === "string" ? draft.payload.summary : "",
    description: typeof draft.payload.description === "string" ? draft.payload.description : "",
    summaryEnglish: typeof draft.payload.summary_english === "string" ? draft.payload.summary_english : "",
  };
}

function buildPayloadPatch(draft: DraftResponse, editorState: DraftEditorState): Record<string, unknown> {
  if (draft.kind === "jira_issue") {
    return {
      summary: editorState.summary.trim(),
      description: editorState.description.trim(),
    };
  }

  return {
    title: editorState.title.trim(),
    summary_english: editorState.summaryEnglish.trim(),
  };
}

function DraftEditorCard({
  accessToken,
  draft,
  meetingId,
  onRefresh,
}: {
  accessToken: string;
  draft: DraftResponse;
  meetingId: string;
  onRefresh: () => Promise<void>;
}) {
  const [editorState, setEditorState] = useState<DraftEditorState>(() => getEditorState(draft));
  const [pendingAction, setPendingAction] = useState<"approve" | "dismiss" | "save" | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setEditorState(getEditorState(draft));
    setError(null);
    setPendingAction(null);
  }, [draft]);

  const isReviewable = draft.status === "draft";
  const payloadPatch = useMemo(() => buildPayloadPatch(draft, editorState), [draft, editorState]);
  const isDirty =
    JSON.stringify(payloadPatch) !== JSON.stringify(buildPayloadPatch(draft, getEditorState(draft)));

  const slackActionItems = Array.isArray(draft.payload.action_items)
    ? (draft.payload.action_items as Array<Record<string, unknown>>)
    : [];

  return (
    <div className="draft-row draft-editor-card">
      <div className="row-title">
        <strong>{draft.kind.replaceAll("_", " ")}</strong>
        <StatusBadge value={draft.status} />
      </div>

      {draft.kind === "jira_issue" ? (
        <div className="draft-form">
          <label className="input-block">
            <span>Issue summary</span>
            <input
              value={editorState.summary}
              onChange={(event) => {
                setEditorState((currentState) => ({ ...currentState, summary: event.target.value }));
              }}
              disabled={!isReviewable || pendingAction !== null}
            />
          </label>
          <label className="input-block">
            <span>Description</span>
            <textarea
              rows={5}
              value={editorState.description}
              onChange={(event) => {
                setEditorState((currentState) => ({ ...currentState, description: event.target.value }));
              }}
              disabled={!isReviewable || pendingAction !== null}
            />
          </label>
        </div>
      ) : (
        <div className="draft-form">
          <label className="input-block">
            <span>Message title</span>
            <input
              value={editorState.title}
              onChange={(event) => {
                setEditorState((currentState) => ({ ...currentState, title: event.target.value }));
              }}
              disabled={!isReviewable || pendingAction !== null}
            />
          </label>
          <label className="input-block">
            <span>English summary</span>
            <textarea
              rows={5}
              value={editorState.summaryEnglish}
              onChange={(event) => {
                setEditorState((currentState) => ({ ...currentState, summaryEnglish: event.target.value }));
              }}
              disabled={!isReviewable || pendingAction !== null}
            />
          </label>
          {slackActionItems.length ? (
            <div className="payload-list">
              <span>Included action items</span>
              <ul>
                {slackActionItems.map((item, index) => (
                  <li key={`${String(item.text)}-${index}`}>
                    <strong>{typeof item.text === "string" ? item.text : "Action item"}</strong>
                    <span>{typeof item.owner_name === "string" && item.owner_name ? item.owner_name : "Unassigned"}</span>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      )}

      {draft.acted_at ? (
        <p className="helper-text">
          Reviewed on {formatDateTime(draft.acted_at)}
          {draft.acted_by_user_id ? " by a workspace member." : "."}
        </p>
      ) : null}

      {error ? <p className="error-text">{error}</p> : null}

      <div className="draft-actions">
        <button
          type="button"
          className="secondary-button"
          disabled={!isReviewable || !isDirty || pendingAction !== null}
          onClick={async () => {
            setPendingAction("save");
            setError(null);
            try {
              await updateDraft(accessToken, meetingId, draft.id, payloadPatch);
              await onRefresh();
            } catch (saveError) {
              setError(saveError instanceof Error ? saveError.message : "Could not save draft changes");
            } finally {
              setPendingAction(null);
            }
          }}
        >
          {pendingAction === "save" ? <LoaderCircle size={16} className="spin" /> : <PencilLine size={16} />}
          <span>Save changes</span>
        </button>
        <button
          type="button"
          className="primary-button"
          disabled={!isReviewable || pendingAction !== null}
          onClick={async () => {
            setPendingAction("approve");
            setError(null);
            try {
              await approveDraft(accessToken, meetingId, draft.id);
              await onRefresh();
            } catch (approveError) {
              setError(approveError instanceof Error ? approveError.message : "Could not approve the draft");
            } finally {
              setPendingAction(null);
            }
          }}
        >
          {pendingAction === "approve" ? <LoaderCircle size={16} className="spin" /> : <Check size={16} />}
          <span>Approve</span>
        </button>
        <button
          type="button"
          className="danger-button"
          disabled={!isReviewable || pendingAction !== null}
          onClick={async () => {
            setPendingAction("dismiss");
            setError(null);
            try {
              await dismissDraft(accessToken, meetingId, draft.id);
              await onRefresh();
            } catch (dismissError) {
              setError(dismissError instanceof Error ? dismissError.message : "Could not dismiss the draft");
            } finally {
              setPendingAction(null);
            }
          }}
        >
          {pendingAction === "dismiss" ? <LoaderCircle size={16} className="spin" /> : <X size={16} />}
          <span>Dismiss</span>
        </button>
      </div>
    </div>
  );
}

export function DraftQueue({ accessToken, meetingId, drafts, onRefresh }: DraftQueueProps) {
  return (
    <div className="stack-list">
      {drafts.length ? (
        drafts.map((draft) => (
          <DraftEditorCard
            key={draft.id}
            accessToken={accessToken}
            draft={draft}
            meetingId={meetingId}
            onRefresh={onRefresh}
          />
        ))
      ) : (
        <div className="empty-state compact">Drafts will appear once the draft stage completes.</div>
      )}
    </div>
  );
}
