"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { formatClock } from "@/lib/format";
import type { TranscriptSegmentResponse } from "@/lib/types";

export interface JumpRequest {
  nonce: number;
  segmentId: string;
}

function findActiveSegmentId(segments: TranscriptSegmentResponse[], currentTime: number): string | null {
  const activeSegment = segments.find(
    (segment) => currentTime >= segment.start_seconds && currentTime <= segment.end_seconds,
  );
  return activeSegment?.id ?? null;
}

export function TranscriptPlayer({
  audioUrl,
  segments,
  jumpRequest,
}: {
  audioUrl: string | null;
  segments: TranscriptSegmentResponse[];
  jumpRequest: JumpRequest | null;
}) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [activeSegmentId, setActiveSegmentId] = useState<string | null>(null);
  const transcriptRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!jumpRequest) {
      return;
    }

    const targetSegment = segments.find((segment) => segment.id === jumpRequest.segmentId);
    if (!targetSegment) {
      return;
    }

    if (audioRef.current) {
      audioRef.current.currentTime = targetSegment.start_seconds;
    }
    setActiveSegmentId(targetSegment.id);

    const targetElement = transcriptRef.current?.querySelector<HTMLElement>(`[data-segment-id="${targetSegment.id}"]`);
    targetElement?.scrollIntoView({ behavior: "smooth", block: "center" });
  }, [jumpRequest, segments]);

  const activeSegment = useMemo(
    () => segments.find((segment) => segment.id === activeSegmentId) ?? null,
    [activeSegmentId, segments],
  );

  return (
    <section className="detail-section">
      <div className="section-heading">
        <div>
          <h2>Transcript</h2>
          <p>Jump through the conversation with timestamps, speaker labels, and language tags.</p>
        </div>
      </div>
      <div className="transcript-layout">
        <div className="player-panel">
          {audioUrl ? (
            <audio
              ref={audioRef}
              controls
              className="audio-player"
              src={audioUrl}
              onTimeUpdate={(event) => {
                const nextActiveSegmentId = findActiveSegmentId(segments, event.currentTarget.currentTime);
                setActiveSegmentId(nextActiveSegmentId);
              }}
            />
          ) : (
            <div className="empty-state compact">Audio will appear here once the meeting file is available.</div>
          )}
          <div className="player-meta">
            <span>Segments: {segments.length}</span>
            <span>{activeSegment ? `Now at ${formatClock(activeSegment.start_seconds)}` : "Ready to scrub"}</span>
          </div>
        </div>
        <div ref={transcriptRef} className="transcript-column">
          {segments.length === 0 ? (
            <div className="empty-state compact">Transcript segments will populate here after processing.</div>
          ) : (
            segments.map((segment) => (
              <button
                key={segment.id}
                type="button"
                className={`transcript-segment${segment.id === activeSegmentId ? " active" : ""}`}
                data-segment-id={segment.id}
                onClick={() => {
                  if (audioRef.current) {
                    audioRef.current.currentTime = segment.start_seconds;
                  }
                  setActiveSegmentId(segment.id);
                }}
              >
                <div className="segment-meta">
                  <span>{formatClock(segment.start_seconds)}</span>
                  <span>{segment.speaker_label ?? "Unknown speaker"}</span>
                  <span>{segment.language_tag ?? "auto"}</span>
                </div>
                <p>{segment.text}</p>
              </button>
            ))
          )}
        </div>
      </div>
    </section>
  );
}
