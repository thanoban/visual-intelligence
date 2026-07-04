"use client";

import Link from "next/link";
import { ArrowLeft, LoaderCircle, RefreshCw, Trash2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { ChatPanel } from "@/components/chat-panel";
import { useSession } from "@/components/session-provider";
import { StatusBadge } from "@/components/status-badge";
import { type JumpRequest, TranscriptPlayer } from "@/components/transcript-player";
import { ApiError, deleteMeeting, fetchMeetingAudioBlob, fetchMeetingDetail, reprocessMeeting } from "@/lib/api";
import { formatClock, formatDateTime, formatDuration } from "@/lib/format";
import type { DraftResponse, MeetingDetailResponse } from "@/lib/types";

function draftPreviewText(draft: DraftResponse): string {
  if (typeof draft.payload.summary === "string") {
    return draft.payload.summary;
  }
  if (typeof draft.payload.text === "string") {
    return draft.payload.text;
  }
  if (typeof draft.payload.description === "string") {
    return draft.payload.description;
  }
  return "Structured draft payload ready for review.";
}

function isMeetingStillRunning(status: string): boolean {
  return status === "uploaded" || status === "processing";
}

export function MeetingDetailClient({ meetingId }: { meetingId: string }) {
  const router = useRouter();
  const { clearSession, hydrated, session } = useSession();
  const [loading, setLoading] = useState(true);
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [meeting, setMeeting] = useState<MeetingDetailResponse | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [jumpRequest, setJumpRequest] = useState<JumpRequest | null>(null);

  const loadMeeting = useCallback(
    async (showLoading: boolean) => {
      if (!session) {
        return;
      }

      if (showLoading) {
        setLoading(true);
      }

      try {
        const nextMeeting = await fetchMeetingDetail(session.access_token, meetingId);
        setMeeting(nextMeeting);
        setError(null);
      } catch (loadError) {
        if (loadError instanceof ApiError && loadError.status === 401) {
          clearSession();
          router.replace("/sign-in");
          return;
        }
        setError(loadError instanceof Error ? loadError.message : "Could not load the meeting");
      } finally {
        setLoading(false);
      }
    },
    [clearSession, meetingId, router, session],
  );

  useEffect(() => {
    if (!hydrated) {
      return;
    }
    if (!session) {
      router.replace("/sign-in");
      return;
    }
    void loadMeeting(true);
  }, [hydrated, loadMeeting, router, session]);

  useEffect(() => {
    if (!meeting || !session || !isMeetingStillRunning(meeting.status)) {
      return;
    }

    const timeoutId = window.setTimeout(() => {
      void loadMeeting(false);
    }, 2500);

    return () => window.clearTimeout(timeoutId);
  }, [loadMeeting, meeting, session]);

  useEffect(() => {
    if (!meeting?.audio_object_key || !session) {
      return;
    }

    let disposed = false;
    void fetchMeetingAudioBlob(session.access_token, meeting.id)
      .then((blob) => {
        const nextUrl = URL.createObjectURL(blob);
        if (disposed) {
          URL.revokeObjectURL(nextUrl);
          return;
        }
        setAudioUrl((currentUrl) => {
          if (currentUrl) {
            URL.revokeObjectURL(currentUrl);
          }
          return nextUrl;
        });
      })
      .catch(() => {
        if (!disposed) {
          setAudioUrl(null);
        }
      });

    return () => {
      disposed = true;
    };
  }, [meeting?.audio_object_key, meeting?.id, session]);

  useEffect(() => {
    return () => {
      setAudioUrl((currentUrl) => {
        if (currentUrl) {
          URL.revokeObjectURL(currentUrl);
        }
        return null;
      });
    };
  }, []);

  const actionItemsWithEvidence = useMemo(() => meeting?.action_items ?? [], [meeting?.action_items]);

  return (
    <AppShell
      title={meeting?.title ?? "Meeting detail"}
      subtitle="Transcript, summaries, evidence-backed action items, drafts, and cited meeting chat in one place."
      actions={
        <div className="inline-actions">
          <Link href="/meetings" className="secondary-button">
            <ArrowLeft size={16} />
            <span>Back</span>
          </Link>
          <button
            type="button"
            className="secondary-button"
            disabled={!meeting || busyAction !== null}
            onClick={async () => {
              if (!session || !meeting) {
                return;
              }
              setBusyAction("reprocess");
              try {
                await reprocessMeeting(session.access_token, meeting.id);
                await loadMeeting(false);
              } finally {
                setBusyAction(null);
              }
            }}
          >
            {busyAction === "reprocess" ? <LoaderCircle size={16} className="spin" /> : <RefreshCw size={16} />}
            <span>Reprocess</span>
          </button>
          <button
            type="button"
            className="danger-button"
            disabled={!meeting || busyAction !== null}
            onClick={async () => {
              if (!session || !meeting) {
                return;
              }
              if (!window.confirm(`Delete ${meeting.title}?`)) {
                return;
              }
              setBusyAction("delete");
              try {
                await deleteMeeting(session.access_token, meeting.id);
                router.replace("/meetings");
              } finally {
                setBusyAction(null);
              }
            }}
          >
            {busyAction === "delete" ? <LoaderCircle size={16} className="spin" /> : <Trash2 size={16} />}
            <span>Delete</span>
          </button>
        </div>
      }
    >
      {loading ? (
        <section className="section-surface">
          <div className="empty-state">Loading meeting detail...</div>
        </section>
      ) : error ? (
        <section className="section-surface">
          <div className="error-text">{error}</div>
        </section>
      ) : meeting ? (
        <>
          <section className="meta-strip">
            <div className="meta-group">
              <StatusBadge value={meeting.status} />
              <StatusBadge value={meeting.language_hint ?? "auto"} />
              {meeting.detected_language ? <StatusBadge value={meeting.detected_language} /> : null}
            </div>
            <div className="meta-group dim">
              <span>{formatDuration(meeting.duration_seconds)}</span>
              <span>{formatDateTime(meeting.updated_at)}</span>
            </div>
          </section>

          <TranscriptPlayer audioUrl={audioUrl} segments={meeting.transcript_segments} jumpRequest={jumpRequest} />

          <section className="summary-grid">
            <article className="section-surface">
              <div className="section-heading">
                <div>
                  <h2>Original-language summary</h2>
                  <p>High-level recap in the meeting&apos;s spoken language mix.</p>
                </div>
              </div>
              <p className="long-copy">{meeting.analysis?.summary_original_language ?? "Waiting for analysis output."}</p>
            </article>
            <article className="section-surface">
              <div className="section-heading">
                <div>
                  <h2>English summary</h2>
                  <p>Cross-team handoff summary for stakeholders and integrations.</p>
                </div>
              </div>
              <p className="long-copy">{meeting.analysis?.summary_english ?? "Waiting for analysis output."}</p>
            </article>
          </section>

          <section className="detail-columns">
            <article className="section-surface">
              <div className="section-heading">
                <div>
                  <h2>Key points</h2>
                  <p>Condensed facts worth carrying into the rest of the team workflow.</p>
                </div>
              </div>
              <div className="stack-list">
                {meeting.analysis?.key_points.length ? (
                  meeting.analysis.key_points.map((item, index) => (
                    <div key={`${item.text}-${index}`} className="text-row">
                      <p>{item.text}</p>
                    </div>
                  ))
                ) : (
                  <div className="empty-state compact">Key points will show up here after the analysis stage completes.</div>
                )}
              </div>
            </article>

            <article className="section-surface">
              <div className="section-heading">
                <div>
                  <h2>Decisions</h2>
                  <p>Tracked decisions with their transcript evidence preserved downstream.</p>
                </div>
              </div>
              <div className="stack-list">
                {meeting.analysis?.decisions.length ? (
                  meeting.analysis.decisions.map((decision, index) => (
                    <div key={`${decision.text}-${index}`} className="text-row">
                      <p>{decision.text}</p>
                    </div>
                  ))
                ) : (
                  <div className="empty-state compact">No decisions recorded yet.</div>
                )}
              </div>
            </article>
          </section>

          <section className="detail-columns">
            <article className="section-surface">
              <div className="section-heading">
                <div>
                  <h2>Action items</h2>
                  <p>Owners, due dates, and transcript evidence in one queue.</p>
                </div>
              </div>
              <div className="stack-list">
                {actionItemsWithEvidence.length ? (
                  actionItemsWithEvidence.map((actionItem) => (
                    <div key={actionItem.id} className="action-row">
                      <div className="row-title">
                        <strong>{actionItem.text}</strong>
                        <StatusBadge value={actionItem.state} />
                      </div>
                      <div className="row-subtitle">
                        <span>{actionItem.owner_name ?? "Unassigned"}</span>
                        <span>{actionItem.due_date ?? "No due date"}</span>
                      </div>
                      <div className="citation-row">
                        {actionItem.evidence_segment_ids.map((segmentId) => {
                          const matchingSegment = meeting.transcript_segments.find((segment) => segment.id === segmentId);
                          if (!matchingSegment) {
                            return null;
                          }
                          return (
                            <button
                              key={segmentId}
                              type="button"
                              className="citation-chip"
                              onClick={() => {
                                setJumpRequest({ nonce: Date.now(), segmentId });
                              }}
                            >
                              <span>{formatClock(matchingSegment.start_seconds)}</span>
                              <span>{matchingSegment.speaker_label ?? "Speaker"}</span>
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="empty-state compact">Action items will show up here when analysis is complete.</div>
                )}
              </div>
            </article>

            <article className="section-surface">
              <div className="section-heading">
                <div>
                  <h2>Draft queue</h2>
                  <p>Reviewable Jira and Slack draft payloads built from the meeting output.</p>
                </div>
              </div>
              <div className="stack-list">
                {meeting.drafts.length ? (
                  meeting.drafts.map((draft) => (
                    <div key={draft.id} className="draft-row">
                      <div className="row-title">
                        <strong>{draft.kind.replaceAll("_", " ")}</strong>
                        <StatusBadge value={draft.status} />
                      </div>
                      <p className="long-copy compact-copy">{draftPreviewText(draft)}</p>
                    </div>
                  ))
                ) : (
                  <div className="empty-state compact">Drafts will appear once the draft stage completes.</div>
                )}
              </div>
            </article>
          </section>

          <ChatPanel
            accessToken={session?.access_token ?? ""}
            disabled={!session || meeting.transcript_segments.length === 0}
            meetingId={meeting.id}
            onJumpToSegment={(segmentId) => {
              setJumpRequest({ nonce: Date.now(), segmentId });
            }}
          />
        </>
      ) : null}
    </AppShell>
  );
}
