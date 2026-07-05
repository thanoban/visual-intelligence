"use client";

import Link from "next/link";
import { LoaderCircle, UserPlus } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useMemo, useState } from "react";

import { AuthShell } from "@/components/auth-shell";
import { useSession } from "@/components/session-provider";
import { acceptInvite } from "@/lib/api";

function InvitePageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { hydrated, saveSession, session } = useSession();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [email, setEmail] = useState(() => searchParams.get("email") ?? "");
  const [password, setPassword] = useState("");

  const token = useMemo(() => searchParams.get("token") ?? "", [searchParams]);
  const linkedEmail = useMemo(() => searchParams.get("email") ?? "", [searchParams]);

  useEffect(() => {
    setEmail(linkedEmail);
  }, [linkedEmail]);

  useEffect(() => {
    if (hydrated && session) {
      router.replace("/meetings");
    }
  }, [hydrated, router, session]);

  const inviteIsValid = Boolean(token && linkedEmail);

  return (
    <AuthShell
      title="Join a workspace"
      subtitle="Accept your VisualSprint invite to review meetings, transcripts, drafts, and cited answers with the rest of the team."
      footer={
        <p>
          Already have an account? <Link href="/sign-in">Sign in</Link>
        </p>
      }
    >
      {inviteIsValid ? (
        <form
          className="stack-form"
          onSubmit={async (event) => {
            event.preventDefault();
            setPending(true);
            setError(null);
            try {
              const nextSession = await acceptInvite({ token, email, name, password });
              saveSession(nextSession);
              router.replace("/meetings");
            } catch (submitError) {
              setError(submitError instanceof Error ? submitError.message : "Invite acceptance failed");
            } finally {
              setPending(false);
            }
          }}
        >
          <label className="input-block">
            <span>Email</span>
            <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
          </label>
          <label className="input-block">
            <span>Your name</span>
            <input value={name} onChange={(event) => setName(event.target.value)} required />
          </label>
          <label className="input-block">
            <span>Password</span>
            <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} minLength={8} required />
          </label>
          {error ? <p className="error-text">{error}</p> : null}
          <div className="form-actions">
            <button type="submit" className="primary-button" disabled={pending}>
              {pending ? <LoaderCircle size={16} className="spin" /> : <UserPlus size={16} />}
              <span>{pending ? "Joining workspace" : "Accept invite"}</span>
            </button>
          </div>
        </form>
      ) : (
        <div className="stack-form">
          <p className="error-text">This invite link is missing the email or token required to join the workspace.</p>
          <p className="helper-text">Ask the workspace owner to send a fresh invite link from the settings page.</p>
        </div>
      )}
    </AuthShell>
  );
}

export default function InvitePage() {
  return (
    <Suspense
      fallback={
        <AuthShell
          title="Join a workspace"
          subtitle="Loading your invite details."
          footer={
            <p>
              Already have an account? <Link href="/sign-in">Sign in</Link>
            </p>
          }
        >
          <div className="empty-state compact">Preparing the invite form...</div>
        </AuthShell>
      }
    >
      <InvitePageContent />
    </Suspense>
  );
}
