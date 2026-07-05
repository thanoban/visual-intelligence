"use client";

import Link from "next/link";
import { ArrowRight, BadgeCheck, CircleAlert, LoaderCircle, RefreshCw, Search, Trash2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { MeetingUploadForm } from "@/components/meeting-upload-form";
import { useSession } from "@/components/session-provider";
import { StatusBadge } from "@/components/status-badge";
import { ApiError, deleteMeeting, listMeetings, reprocessMeeting, uploadMeeting } from "@/lib/api";
import { formatDateTime, formatDuration } from "@/lib/format";
import type { MeetingSummary } from "@/lib/types";

function isMeetingInFlight(status: string): boolean {
  return status === "uploaded" || status === "processing";
}

export default function MeetingsPage() {
  const router = useRouter();
  const { clearSession, hydrated, session } = useSession();
  const [meetings, setMeetings] = useState<MeetingSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [busyMeetingId, setBusyMeetingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  const loadMeetings = useCallback(
    async (showLoading: boolean, searchQuery: string) => {
      if (!session) {
        return;
      }

      if (showLoading) {
        setLoading(true);
      }

      try {
        const response = await listMeetings(session.access_token, searchQuery);
        setMeetings(response.items);
        setError(null);
      } catch (loadError) {
        if (loadError instanceof ApiError && loadError.status === 401) {
          clearSession();
          router.replace("/sign-in");
          return;
        }
        setError(loadError instanceof Error ? loadError.message : "Could not load meetings");
      } finally {
        setLoading(false);
      }
    },
    [clearSession, router, session],
  );

  useEffect(() => {
    if (!hydrated) {
      return;
    }
    if (!session) {
      router.replace("/sign-in");
      return;
    }
    void loadMeetings(true, "");
  }, [hydrated, loadMeetings, router, session]);

  useEffect(() => {
    if (!hydrated || !session) {
      return;
    }

    const timeoutId = window.setTimeout(() => {
      void loadMeetings(false, search);
    }, 250);

    return () => window.clearTimeout(timeoutId);
  }, [hydrated, loadMeetings, search, session]);

  useEffect(() => {
    if (!meetings.some((meeting) => isMeetingInFlight(meeting.status))) {
      return;
    }

    const timeoutId = window.setTimeout(() => {
      void loadMeetings(false, search);
    }, 2500);

    return () => window.clearTimeout(timeoutId);
  }, [loadMeetings, meetings, search]);

  const completedCount = meetings.filter((meeting) => meeting.status === "completed").length;
  const processingCount = meetings.filter((meeting) => isMeetingInFlight(meeting.status)).length;
  const failedCount = meetings.filter((meeting) => meeting.status === "failed").length;

  return (
    <AppShell
      title="Meetings"
      subtitle="Upload recordings, monitor processing, and open the full transcript-and-draft workflow for each meeting."
      actions={
        <button
          type="button"
          className="secondary-button"
          onClick={() => void loadMeetings(false, search)}
          disabled={loading}
        >
          <RefreshCw size={16} />
          <span>Refresh</span>
        </button>
      }
    >
      <section className="dashboard-grid">
        <MeetingUploadForm
          busy={uploading}
          onUpload={async (payload) => {
            if (!session) {
              return;
            }
            setUploading(true);
            try {
              await uploadMeeting(session.access_token, payload);
              await loadMeetings(false, search);
            } finally {
              setUploading(false);
            }
          }}
        />

        <section className="section-surface">
          <div className="section-heading">
            <div>
              <h2>Queue overview</h2>
              <p>Keep an eye on progress, then jump straight into the meeting that needs attention.</p>
            </div>
          </div>
          <div className="stats-row">
            <div className="stat-tile">
              <BadgeCheck size={18} />
              <strong>{completedCount}</strong>
              <span>Completed</span>
            </div>
            <div className="stat-tile">
              <LoaderCircle size={18} className={processingCount ? "spin" : ""} />
              <strong>{processingCount}</strong>
              <span>Processing</span>
            </div>
            <div className="stat-tile">
              <CircleAlert size={18} />
              <strong>{failedCount}</strong>
              <span>Failed</span>
            </div>
          </div>
          <label className="search-field">
              <Search size={16} />
              <input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search by title or transcript text"
              />
            </label>
          {error ? <p className="error-text">{error}</p> : null}
          <div className="meeting-list">
            {loading ? (
              <div className="empty-state compact">Loading meetings...</div>
            ) : meetings.length ? (
              meetings.map((meeting) => (
                <article key={meeting.id} className="meeting-row">
                  <div className="meeting-copy">
                    <div className="row-title">
                      <strong>{meeting.title}</strong>
                      <StatusBadge value={meeting.status} />
                    </div>
                    <div className="row-subtitle">
                      <span>{formatDateTime(meeting.created_at)}</span>
                      <span>{formatDuration(meeting.duration_seconds)}</span>
                      <span>{meeting.detected_language ?? meeting.language_hint ?? "auto"}</span>
                    </div>
                    {meeting.error_reason ? <p className="error-text compact-copy">{meeting.error_reason}</p> : null}
                  </div>
                  <div className="row-actions">
                    <button
                      type="button"
                      className="icon-button"
                      onClick={async () => {
                        if (!session) {
                          return;
                        }
                        setBusyMeetingId(meeting.id);
                        try {
                          await reprocessMeeting(session.access_token, meeting.id);
                          await loadMeetings(false, search);
                        } finally {
                          setBusyMeetingId(null);
                        }
                      }}
                      disabled={busyMeetingId === meeting.id}
                      aria-label={`Reprocess ${meeting.title}`}
                    >
                      {busyMeetingId === meeting.id ? <LoaderCircle size={16} className="spin" /> : <RefreshCw size={16} />}
                    </button>
                    <button
                      type="button"
                      className="icon-button"
                      onClick={async () => {
                        if (!session) {
                          return;
                        }
                        if (!window.confirm(`Delete ${meeting.title}?`)) {
                          return;
                        }
                        setBusyMeetingId(meeting.id);
                        try {
                          await deleteMeeting(session.access_token, meeting.id);
                          await loadMeetings(false, search);
                        } finally {
                          setBusyMeetingId(null);
                        }
                      }}
                      disabled={busyMeetingId === meeting.id}
                      aria-label={`Delete ${meeting.title}`}
                    >
                      <Trash2 size={16} />
                    </button>
                    <Link href={`/meetings/${meeting.id}`} className="primary-button compact-button">
                      <span>Open</span>
                      <ArrowRight size={16} />
                    </Link>
                  </div>
                </article>
              ))
            ) : (
              <div className="empty-state compact">
                {search.trim()
                  ? "No meetings matched that title or transcript text yet."
                  : "No meetings yet. Upload a recording to start the pipeline."}
              </div>
            )}
          </div>
        </section>
      </section>
    </AppShell>
  );
}
