export interface WorkspaceSummary {
  id: string;
  name: string;
  settings: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface UserSummary {
  id: string;
  email: string;
  name: string;
  role: string;
  workspace_id: string;
  created_at: string;
  updated_at: string;
}

export interface AuthSessionResponse {
  access_token: string;
  token_type: string;
  user: UserSummary;
  workspace: WorkspaceSummary;
}

export interface InviteResponse {
  id: string;
  email: string;
  status: string;
  token: string;
  workspace_id: string;
  invited_by_user_id: string | null;
  expires_at: string | null;
  accepted_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface WorkspaceIntegrationStatus {
  provider: string;
  connected: boolean;
}

export interface WorkspaceSettingsResponse {
  workspace: WorkspaceSummary;
  integrations: WorkspaceIntegrationStatus[];
}

export interface WorkspaceMembersResponse {
  members: UserSummary[];
  invites: InviteResponse[];
}

export interface UpdateWorkspaceSettingsPayload {
  default_language_hint: string;
  slack_channel: string;
  slack_auto_post: boolean;
}

export interface MeetingSummary {
  id: string;
  workspace_id: string;
  title: string;
  source: string;
  status: string;
  language_hint: string | null;
  detected_language: string | null;
  duration_seconds: number | null;
  audio_object_key: string | null;
  error_reason: string | null;
  created_at: string;
  updated_at: string;
}

export interface TranscriptSegmentResponse {
  id: string;
  index: number;
  start_seconds: number;
  end_seconds: number;
  speaker_label: string | null;
  text: string;
  language_tag: string | null;
}

export interface MeetingAnalysisResponse {
  id: string;
  summary_original_language: string;
  summary_english: string;
  key_points: Array<{ text: string; evidence_segment_ids: string[] }>;
  decisions: Array<{ text: string; evidence_segment_ids: string[] }>;
}

export interface ActionItemResponse {
  id: string;
  text: string;
  owner_name: string | null;
  owner_user_id: string | null;
  due_date: string | null;
  evidence_segment_ids: string[];
  state: string;
}

export interface DraftResponse {
  id: string;
  action_item_id: string | null;
  kind: string;
  payload: Record<string, unknown>;
  status: string;
  external_reference: string | null;
  acted_by_user_id: string | null;
  acted_at: string | null;
}

export interface UpdateDraftPayload {
  payload: Record<string, unknown>;
}

export interface MeetingDetailResponse extends MeetingSummary {
  transcript_segments: TranscriptSegmentResponse[];
  analysis: MeetingAnalysisResponse | null;
  action_items: ActionItemResponse[];
  drafts: DraftResponse[];
}

export interface MeetingListResponse {
  items: MeetingSummary[];
  total: number;
}

export interface ReprocessResponse {
  id: string;
  status: string;
}

export interface MeetingAnswerCitationResponse {
  segment_id: string;
  start_seconds: number;
  end_seconds: number;
  speaker_label: string | null;
  text: string;
}

export interface MeetingQuestionResponse {
  answer_text: string;
  not_discussed: boolean;
  citations: MeetingAnswerCitationResponse[];
}
