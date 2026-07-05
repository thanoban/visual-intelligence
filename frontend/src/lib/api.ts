import type {
  AuthSessionResponse,
  DraftResponse,
  MeetingDetailResponse,
  MeetingListResponse,
  MeetingQuestionResponse,
  ReprocessResponse,
  UpdateWorkspaceSettingsPayload,
  WorkspaceSettingsResponse,
} from "@/lib/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function buildHeaders(token?: string, init?: HeadersInit): Headers {
  const headers = new Headers(init);
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  return headers;
}

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let detail = "Request failed";
    try {
      const body = (await response.json()) as { detail?: string };
      if (typeof body.detail === "string" && body.detail) {
        detail = body.detail;
      }
    } catch {
      // Ignore JSON parse failures for error bodies.
    }
    throw new ApiError(response.status, detail);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export function buildApiUrl(path: string): string {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${API_BASE_URL}${normalizedPath}`;
}

export async function signIn(email: string, password: string): Promise<AuthSessionResponse> {
  const response = await fetch(buildApiUrl("/auth/sign-in"), {
    method: "POST",
    headers: buildHeaders(undefined, { "Content-Type": "application/json" }),
    body: JSON.stringify({ email, password }),
  });
  return parseResponse<AuthSessionResponse>(response);
}

export async function signUp(payload: {
  email: string;
  name: string;
  password: string;
  workspaceName: string;
}): Promise<AuthSessionResponse> {
  const response = await fetch(buildApiUrl("/auth/sign-up"), {
    method: "POST",
    headers: buildHeaders(undefined, { "Content-Type": "application/json" }),
    body: JSON.stringify({
      email: payload.email,
      name: payload.name,
      password: payload.password,
      workspace_name: payload.workspaceName,
    }),
  });
  return parseResponse<AuthSessionResponse>(response);
}

export async function fetchSession(token: string): Promise<AuthSessionResponse> {
  const response = await fetch(buildApiUrl("/auth/session"), {
    headers: buildHeaders(token),
  });
  return parseResponse<AuthSessionResponse>(response);
}

export async function listMeetings(token: string): Promise<MeetingListResponse> {
  const response = await fetch(buildApiUrl("/meetings"), {
    headers: buildHeaders(token),
  });
  return parseResponse<MeetingListResponse>(response);
}

export async function uploadMeeting(
  token: string,
  payload: {
    file: File;
    title: string;
    languageHint: string;
  },
): Promise<void> {
  const formData = new FormData();
  formData.set("file", payload.file);
  formData.set("title", payload.title);
  formData.set("language_hint", payload.languageHint);

  const response = await fetch(buildApiUrl("/meetings/upload"), {
    method: "POST",
    headers: buildHeaders(token),
    body: formData,
  });
  await parseResponse(response);
}

export async function fetchMeetingDetail(token: string, meetingId: string): Promise<MeetingDetailResponse> {
  const response = await fetch(buildApiUrl(`/meetings/${meetingId}`), {
    headers: buildHeaders(token),
  });
  return parseResponse<MeetingDetailResponse>(response);
}

export async function fetchMeetingAudioBlob(token: string, meetingId: string): Promise<Blob> {
  const response = await fetch(buildApiUrl(`/meetings/${meetingId}/audio`), {
    headers: buildHeaders(token),
  });
  if (!response.ok) {
    throw new ApiError(response.status, "Could not load meeting audio");
  }
  return response.blob();
}

export async function reprocessMeeting(token: string, meetingId: string): Promise<ReprocessResponse> {
  const response = await fetch(buildApiUrl(`/meetings/${meetingId}/reprocess`), {
    method: "POST",
    headers: buildHeaders(token),
  });
  return parseResponse<ReprocessResponse>(response);
}

export async function deleteMeeting(token: string, meetingId: string): Promise<void> {
  const response = await fetch(buildApiUrl(`/meetings/${meetingId}`), {
    method: "DELETE",
    headers: buildHeaders(token),
  });
  await parseResponse(response);
}

export async function askMeetingQuestion(
  token: string,
  meetingId: string,
  question: string,
): Promise<MeetingQuestionResponse> {
  const response = await fetch(buildApiUrl(`/meetings/${meetingId}/chat`), {
    method: "POST",
    headers: buildHeaders(token, { "Content-Type": "application/json" }),
    body: JSON.stringify({ question }),
  });
  return parseResponse<MeetingQuestionResponse>(response);
}

export async function updateDraft(
  token: string,
  meetingId: string,
  draftId: string,
  payload: Record<string, unknown>,
): Promise<DraftResponse> {
  const response = await fetch(buildApiUrl(`/meetings/${meetingId}/drafts/${draftId}`), {
    method: "PATCH",
    headers: buildHeaders(token, { "Content-Type": "application/json" }),
    body: JSON.stringify({ payload }),
  });
  return parseResponse<DraftResponse>(response);
}

export async function approveDraft(token: string, meetingId: string, draftId: string): Promise<DraftResponse> {
  const response = await fetch(buildApiUrl(`/meetings/${meetingId}/drafts/${draftId}/approve`), {
    method: "POST",
    headers: buildHeaders(token),
  });
  return parseResponse<DraftResponse>(response);
}

export async function dismissDraft(token: string, meetingId: string, draftId: string): Promise<DraftResponse> {
  const response = await fetch(buildApiUrl(`/meetings/${meetingId}/drafts/${draftId}/dismiss`), {
    method: "POST",
    headers: buildHeaders(token),
  });
  return parseResponse<DraftResponse>(response);
}

export async function fetchWorkspaceSettings(token: string): Promise<WorkspaceSettingsResponse> {
  const response = await fetch(buildApiUrl("/workspace/settings"), {
    headers: buildHeaders(token),
  });
  return parseResponse<WorkspaceSettingsResponse>(response);
}

export async function updateWorkspaceSettings(
  token: string,
  payload: UpdateWorkspaceSettingsPayload,
): Promise<WorkspaceSettingsResponse> {
  const response = await fetch(buildApiUrl("/workspace/settings"), {
    method: "PATCH",
    headers: buildHeaders(token, { "Content-Type": "application/json" }),
    body: JSON.stringify(payload),
  });
  return parseResponse<WorkspaceSettingsResponse>(response);
}
