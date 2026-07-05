"use client";

import { Copy, LoaderCircle, MailPlus, Save } from "lucide-react";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { StatusBadge } from "@/components/status-badge";
import { useSession } from "@/components/session-provider";
import { ApiError, createInvite, fetchWorkspaceMembers, fetchWorkspaceSettings, updateWorkspaceSettings } from "@/lib/api";
import { formatDateTime } from "@/lib/format";
import type { InviteResponse, UserSummary, WorkspaceIntegrationStatus } from "@/lib/types";

interface SettingsFormState {
  defaultLanguageHint: string;
  slackChannel: string;
  slackAutoPost: boolean;
}

const DEFAULT_FORM_STATE: SettingsFormState = {
  defaultLanguageHint: "auto",
  slackChannel: "",
  slackAutoPost: false,
};

function getSettingsFormState(settings: Record<string, unknown> | undefined): SettingsFormState {
  return {
    defaultLanguageHint:
      typeof settings?.default_language_hint === "string" ? settings.default_language_hint : DEFAULT_FORM_STATE.defaultLanguageHint,
    slackChannel: typeof settings?.slack_channel === "string" ? settings.slack_channel : DEFAULT_FORM_STATE.slackChannel,
    slackAutoPost: typeof settings?.slack_auto_post === "boolean" ? settings.slack_auto_post : DEFAULT_FORM_STATE.slackAutoPost,
  };
}

export default function SettingsPage() {
  const router = useRouter();
  const { clearSession, hydrated, refreshSession, session } = useSession();
  const [formState, setFormState] = useState<SettingsFormState>(() => getSettingsFormState(session?.workspace.settings));
  const [integrations, setIntegrations] = useState<WorkspaceIntegrationStatus[]>([]);
  const [members, setMembers] = useState<UserSummary[]>([]);
  const [invites, setInvites] = useState<InviteResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [invitePending, setInvitePending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteError, setInviteError] = useState<string | null>(null);
  const [inviteNotice, setInviteNotice] = useState<string | null>(null);

  const loadWorkspace = useCallback(async () => {
    if (!session) {
      return;
    }

    setLoading(true);
    try {
      const [settingsResponse, membersResponse] = await Promise.all([
        fetchWorkspaceSettings(session.access_token),
        fetchWorkspaceMembers(session.access_token),
      ]);
      setFormState(getSettingsFormState(settingsResponse.workspace.settings));
      setIntegrations(settingsResponse.integrations);
      setMembers(membersResponse.members);
      setInvites(membersResponse.invites);
      setError(null);
    } catch (loadError) {
      if (loadError instanceof ApiError && loadError.status === 401) {
        clearSession();
        router.replace("/sign-in");
        return;
      }
      setError(loadError instanceof Error ? loadError.message : "Could not load workspace settings");
    } finally {
      setLoading(false);
    }
  }, [clearSession, router, session]);

  useEffect(() => {
    if (!hydrated) {
      return;
    }
    if (!session) {
      router.replace("/sign-in");
      return;
    }
    void loadWorkspace();
  }, [hydrated, loadWorkspace, router, session]);

  const isOwner = session?.user.role === "owner";
  const isDirty = useMemo(() => {
    const currentSettings = getSettingsFormState(session?.workspace.settings);
    return JSON.stringify(currentSettings) !== JSON.stringify(formState);
  }, [formState, session?.workspace.settings]);

  return (
    <AppShell
      title="Workspace settings"
      subtitle="Set the default language hint, decide how Slack posting should behave, and keep an eye on which integrations are ready."
      actions={
        <button
          type="button"
          className="primary-button"
          disabled={!isOwner || !isDirty || saving || loading || !session}
          onClick={async () => {
            if (!session) {
              return;
            }
            setSaving(true);
            setNotice(null);
            setError(null);
            try {
              const response = await updateWorkspaceSettings(session.access_token, {
                default_language_hint: formState.defaultLanguageHint,
                slack_channel: formState.slackChannel,
                slack_auto_post: formState.slackAutoPost,
              });
              setFormState(getSettingsFormState(response.workspace.settings));
              setIntegrations(response.integrations);
              await refreshSession();
              setNotice("Workspace settings saved.");
            } catch (saveError) {
              if (saveError instanceof ApiError && saveError.status === 401) {
                clearSession();
                router.replace("/sign-in");
                return;
              }
              setError(saveError instanceof Error ? saveError.message : "Could not save workspace settings");
            } finally {
              setSaving(false);
            }
          }}
        >
          {saving ? <LoaderCircle size={16} className="spin" /> : <Save size={16} />}
          <span>Save settings</span>
        </button>
      }
    >
      <section className="dashboard-grid settings-grid">
        <article className="section-surface">
          <div className="section-heading">
            <div>
              <h2>Defaults and delivery</h2>
              <p>These choices shape the upload flow now and the Slack integration path once it is connected.</p>
            </div>
          </div>
          {loading ? (
            <div className="empty-state compact">Loading workspace settings...</div>
          ) : (
            <div className="stack-form">
              <label className="input-block">
                <span>Default language hint</span>
                <select
                  value={formState.defaultLanguageHint}
                  onChange={(event) => {
                    setFormState((currentState) => ({
                      ...currentState,
                      defaultLanguageHint: event.target.value,
                    }));
                    setNotice(null);
                  }}
                  disabled={!isOwner || saving}
                >
                  <option value="auto">Auto-detect</option>
                  <option value="en">English</option>
                  <option value="si">Sinhala</option>
                  <option value="ta">Tamil</option>
                </select>
              </label>

              <label className="input-block">
                <span>Default Slack channel</span>
                <input
                  value={formState.slackChannel}
                  onChange={(event) => {
                    setFormState((currentState) => ({
                      ...currentState,
                      slackChannel: event.target.value,
                    }));
                    setNotice(null);
                  }}
                  placeholder="#delivery"
                  disabled={!isOwner || saving}
                />
              </label>

              <label className="checkbox-row">
                <input
                  type="checkbox"
                  checked={formState.slackAutoPost}
                  onChange={(event) => {
                    setFormState((currentState) => ({
                      ...currentState,
                      slackAutoPost: event.target.checked,
                    }));
                    setNotice(null);
                  }}
                  disabled={!isOwner || saving}
                />
                <span className="checkbox-copy">
                  <strong>Automatically post the Slack summary after processing</strong>
                  <span>The setting is stored now and will activate the notify stage once Slack delivery lands.</span>
                </span>
              </label>

              {!isOwner ? <p className="helper-text">Only workspace owners can update these settings.</p> : null}
              {notice ? <p className="helper-text">{notice}</p> : null}
              {error ? <p className="error-text">{error}</p> : null}
            </div>
          )}
        </article>

        <article className="section-surface">
          <div className="section-heading">
            <div>
              <h2>Integration status</h2>
              <p>These badges track which external systems are already connected for this workspace.</p>
            </div>
          </div>
          {loading ? (
            <div className="empty-state compact">Loading integration status...</div>
          ) : (
            <div className="integration-list">
              {integrations.map((integration) => (
                <div key={integration.provider} className="integration-row">
                  <div className="integration-copy">
                    <strong>{integration.provider.toUpperCase()}</strong>
                    <span>
                      {integration.connected
                        ? "Ready for workspace-level actions."
                        : "Not connected yet for this workspace."}
                    </span>
                  </div>
                  <StatusBadge value={integration.connected ? "connected" : "not_connected"} />
                </div>
              ))}
            </div>
          )}
        </article>

        <article className="section-surface">
          <div className="section-heading">
            <div>
              <h2>Members and invites</h2>
              <p>Invite teammates by email, keep track of pending access, and share the acceptance link while email delivery is still manual.</p>
            </div>
          </div>
          {loading ? (
            <div className="empty-state compact">Loading members and invites...</div>
          ) : (
            <div className="stack-form">
              {isOwner ? (
                <form
                  className="invite-form"
                  onSubmit={async (event) => {
                    event.preventDefault();
                    if (!session) {
                      return;
                    }
                    setInvitePending(true);
                    setInviteError(null);
                    setInviteNotice(null);
                    try {
                      await createInvite(session.access_token, inviteEmail);
                      setInviteEmail("");
                      setInviteNotice("Invite created. Share the acceptance link from the pending invites list.");
                      const refreshedMembers = await fetchWorkspaceMembers(session.access_token);
                      setMembers(refreshedMembers.members);
                      setInvites(refreshedMembers.invites);
                    } catch (submitError) {
                      if (submitError instanceof ApiError && submitError.status === 401) {
                        clearSession();
                        router.replace("/sign-in");
                        return;
                      }
                      setInviteError(submitError instanceof Error ? submitError.message : "Could not create invite");
                    } finally {
                      setInvitePending(false);
                    }
                  }}
                >
                  <label className="input-block">
                    <span>Invite by email</span>
                    <input
                      type="email"
                      value={inviteEmail}
                      onChange={(event) => setInviteEmail(event.target.value)}
                      placeholder="teammate@example.com"
                      required
                    />
                  </label>
                  <div className="form-actions">
                    <button type="submit" className="secondary-button" disabled={invitePending}>
                      {invitePending ? <LoaderCircle size={16} className="spin" /> : <MailPlus size={16} />}
                      <span>{invitePending ? "Sending invite" : "Create invite"}</span>
                    </button>
                  </div>
                </form>
              ) : (
                <p className="helper-text">Only workspace owners can create invites, but every member can see who already has access.</p>
              )}

              {inviteNotice ? <p className="helper-text">{inviteNotice}</p> : null}
              {inviteError ? <p className="error-text">{inviteError}</p> : null}

              <div className="team-list">
                {members.map((member) => (
                  <div key={member.id} className="team-row">
                    <div className="team-copy">
                      <strong>{member.name}</strong>
                      <span>{member.email}</span>
                    </div>
                    <StatusBadge value={member.role} />
                  </div>
                ))}
              </div>

              <div className="pending-section">
                <div className="section-heading compact-heading">
                  <div>
                    <h3>Pending invites</h3>
                    <p>Copy the acceptance link and send it through email or chat until outbound mail is wired in.</p>
                  </div>
                </div>
                {invites.filter((invite) => invite.status === "pending").length ? (
                  <div className="team-list">
                    {invites
                      .filter((invite) => invite.status === "pending")
                      .map((invite) => (
                        <div key={invite.id} className="team-row">
                          <div className="team-copy">
                            <strong>{invite.email}</strong>
                            <span>Expires {invite.expires_at ? formatDateTime(invite.expires_at) : "soon"}</span>
                          </div>
                          <div className="invite-actions">
                            <button
                              type="button"
                              className="icon-button"
                              aria-label={`Copy invite link for ${invite.email}`}
                              onClick={async () => {
                                try {
                                  const inviteUrl = `${window.location.origin}/invite?token=${encodeURIComponent(invite.token)}&email=${encodeURIComponent(invite.email)}`;
                                  await navigator.clipboard.writeText(inviteUrl);
                                  setInviteNotice(`Invite link copied for ${invite.email}.`);
                                  setInviteError(null);
                                } catch {
                                  setInviteError(`Could not copy the invite link for ${invite.email}.`);
                                }
                              }}
                            >
                              <Copy size={16} />
                            </button>
                            <StatusBadge value={invite.status} />
                          </div>
                        </div>
                      ))}
                  </div>
                ) : (
                  <div className="empty-state compact">No pending invites right now.</div>
                )}
              </div>
            </div>
          )}
        </article>
      </section>
    </AppShell>
  );
}
