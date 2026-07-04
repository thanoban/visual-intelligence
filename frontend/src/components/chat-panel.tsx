"use client";

import { LoaderCircle, MessageSquareText } from "lucide-react";
import { useState } from "react";

import { askMeetingQuestion } from "@/lib/api";
import { formatClock } from "@/lib/format";
import type { MeetingQuestionResponse } from "@/lib/types";

interface ConversationEntry {
  id: number;
  question: string;
  response: MeetingQuestionResponse | null;
  error: string | null;
}

export function ChatPanel({
  accessToken,
  disabled,
  meetingId,
  onJumpToSegment,
}: {
  accessToken: string;
  disabled: boolean;
  meetingId: string;
  onJumpToSegment: (segmentId: string) => void;
}) {
  const [entries, setEntries] = useState<ConversationEntry[]>([]);
  const [pending, setPending] = useState(false);
  const [question, setQuestion] = useState("");

  return (
    <section className="detail-section">
      <div className="section-heading">
        <div>
          <h2>Ask the meeting</h2>
          <p>Query the transcript in English, Sinhala, or Tamil and jump straight to cited evidence.</p>
        </div>
      </div>
      <form
        className="chat-form"
        onSubmit={async (event) => {
          event.preventDefault();
          const trimmedQuestion = question.trim();
          if (!trimmedQuestion || pending || disabled) {
            return;
          }

          const entryId = Date.now();
          setPending(true);
          setQuestion("");
          setEntries((currentEntries) => [
            { id: entryId, question: trimmedQuestion, response: null, error: null },
            ...currentEntries,
          ]);

          try {
            const response = await askMeetingQuestion(accessToken, meetingId, trimmedQuestion);
            setEntries((currentEntries) =>
              currentEntries.map((entry) =>
                entry.id === entryId ? { ...entry, response, error: null } : entry,
              ),
            );
          } catch (error) {
            const message = error instanceof Error ? error.message : "Question failed";
            setEntries((currentEntries) =>
              currentEntries.map((entry) =>
                entry.id === entryId ? { ...entry, error: message } : entry,
              ),
            );
          } finally {
            setPending(false);
          }
        }}
      >
        <textarea
          rows={3}
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="mokakda deploy eka gena decide kale?"
          disabled={disabled}
        />
        <div className="form-actions">
          <button type="submit" className="primary-button" disabled={pending || disabled}>
            {pending ? <LoaderCircle size={16} className="spin" /> : <MessageSquareText size={16} />}
            <span>{pending ? "Asking" : "Ask question"}</span>
          </button>
        </div>
      </form>
      <div className="chat-history">
        {entries.length === 0 ? (
          <div className="empty-state compact">Your meeting questions and cited answers will show up here.</div>
        ) : (
          entries.map((entry) => (
            <article key={entry.id} className="chat-entry">
              <h3>{entry.question}</h3>
              {entry.error ? <p className="error-text">{entry.error}</p> : null}
              {entry.response ? (
                <div className="chat-answer">
                  <p>{entry.response.answer_text}</p>
                  <div className="citation-row">
                    {entry.response.citations.map((citation) => (
                      <button
                        key={citation.segment_id}
                        type="button"
                        className="citation-chip"
                        onClick={() => onJumpToSegment(citation.segment_id)}
                      >
                        <span>{formatClock(citation.start_seconds)}</span>
                        <span>{citation.speaker_label ?? "Speaker"}</span>
                      </button>
                    ))}
                  </div>
                </div>
              ) : null}
            </article>
          ))
        )}
      </div>
    </section>
  );
}
