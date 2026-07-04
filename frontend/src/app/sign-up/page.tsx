"use client";

import Link from "next/link";
import { LoaderCircle, UserPlus } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AuthShell } from "@/components/auth-shell";
import { useSession } from "@/components/session-provider";
import { signUp } from "@/lib/api";

export default function SignUpPage() {
  const router = useRouter();
  const { hydrated, saveSession, session } = useSession();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [workspaceName, setWorkspaceName] = useState("");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  useEffect(() => {
    if (hydrated && session) {
      router.replace("/meetings");
    }
  }, [hydrated, router, session]);

  return (
    <AuthShell
      title="Create a team workspace"
      subtitle="Stand up a shared meeting intelligence workspace with transcript-backed summaries, action items, drafts, and chat."
      footer={
        <p>
          Already have access? <Link href="/sign-in">Sign in</Link>
        </p>
      }
    >
      <form
        className="stack-form"
        onSubmit={async (event) => {
          event.preventDefault();
          setPending(true);
          setError(null);
          try {
            const nextSession = await signUp({ workspaceName, name, email, password });
            saveSession(nextSession);
            router.replace("/meetings");
          } catch (submitError) {
            setError(submitError instanceof Error ? submitError.message : "Sign-up failed");
          } finally {
            setPending(false);
          }
        }}
      >
        <label className="input-block">
          <span>Workspace name</span>
          <input value={workspaceName} onChange={(event) => setWorkspaceName(event.target.value)} required />
        </label>
        <div className="field-row">
          <label className="input-block">
            <span>Your name</span>
            <input value={name} onChange={(event) => setName(event.target.value)} required />
          </label>
          <label className="input-block">
            <span>Email</span>
            <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
          </label>
        </div>
        <label className="input-block">
          <span>Password</span>
          <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} minLength={8} required />
        </label>
        {error ? <p className="error-text">{error}</p> : null}
        <div className="form-actions">
          <button type="submit" className="primary-button" disabled={pending}>
            {pending ? <LoaderCircle size={16} className="spin" /> : <UserPlus size={16} />}
            <span>{pending ? "Creating workspace" : "Create workspace"}</span>
          </button>
        </div>
      </form>
    </AuthShell>
  );
}
