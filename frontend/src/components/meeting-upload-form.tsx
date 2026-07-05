"use client";

import { LoaderCircle, Upload } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

function normalizeLanguageHint(value: string | undefined): string {
  return value === "en" || value === "si" || value === "ta" ? value : "auto";
}

function formatLanguageHintLabel(value: string): string {
  if (value === "en") {
    return "English";
  }
  if (value === "si") {
    return "Sinhala";
  }
  if (value === "ta") {
    return "Tamil";
  }
  return "Auto-detect";
}

export function MeetingUploadForm({
  busy,
  defaultLanguageHint,
  onUpload,
}: {
  busy: boolean;
  defaultLanguageHint?: string;
  onUpload: (payload: { file: File; title: string; languageHint: string }) => Promise<void>;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const resolvedDefaultLanguageHint = useMemo(
    () => normalizeLanguageHint(defaultLanguageHint),
    [defaultLanguageHint],
  );
  const [languageHint, setLanguageHint] = useState(() => normalizeLanguageHint(defaultLanguageHint));
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLanguageHint(resolvedDefaultLanguageHint);
  }, [resolvedDefaultLanguageHint]);

  return (
    <section className="section-surface">
      <div className="section-heading">
        <div>
          <h2>Upload a meeting</h2>
          <p>Drop in an audio or video recording to run the transcript, analysis, and draft flow.</p>
        </div>
      </div>
      <form
        className="stack-form"
        onSubmit={async (event) => {
          event.preventDefault();
          if (!file) {
            setError("Choose an audio or video file first.");
            return;
          }

          setError(null);
          const trimmedTitle = title.trim() || file.name.replace(/\.[^.]+$/, "");
          try {
            await onUpload({ file, title: trimmedTitle, languageHint });
            setFile(null);
            setTitle("");
            setLanguageHint(resolvedDefaultLanguageHint);
            const input = event.currentTarget.elements.namedItem("meeting-file");
            if (input instanceof HTMLInputElement) {
              input.value = "";
            }
          } catch (submitError) {
            setError(submitError instanceof Error ? submitError.message : "Upload failed");
          }
        }}
      >
        <label className="input-block">
          <span>Meeting file</span>
          <input
            id="meeting-file"
            name="meeting-file"
            type="file"
            accept=".mp3,.m4a,.wav,.mp4,.webm,.flac"
            onChange={(event) => {
              setFile(event.target.files?.[0] ?? null);
            }}
          />
        </label>
        <div className="field-row">
          <label className="input-block">
            <span>Title</span>
            <input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Weekly delivery standup" />
          </label>
          <label className="input-block">
            <span>Language hint</span>
            <select value={languageHint} onChange={(event) => setLanguageHint(event.target.value)}>
              <option value="auto">Auto-detect</option>
              <option value="en">English</option>
              <option value="si">Sinhala</option>
              <option value="ta">Tamil</option>
            </select>
          </label>
        </div>
        {file ? (
          <p className="helper-text">
            Selected: {file.name}. Default language hint: {formatLanguageHintLabel(resolvedDefaultLanguageHint)}.
          </p>
        ) : null}
        {error ? <p className="error-text">{error}</p> : null}
        <div className="form-actions">
          <button type="submit" className="primary-button" disabled={busy}>
            {busy ? <LoaderCircle size={16} className="spin" /> : <Upload size={16} />}
            <span>{busy ? "Uploading" : "Upload meeting"}</span>
          </button>
        </div>
      </form>
    </section>
  );
}
