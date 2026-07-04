"use client";

import Link from "next/link";
import { LoaderCircle, LogIn } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AuthShell } from "@/components/auth-shell";
import { useSession } from "@/components/session-provider";
import { signIn } from "@/lib/api";

export default function SignInPage() {
  const router = useRouter();
  const { hydrated, saveSession, session } = useSession();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  useEffect(() => {
    if (hydrated && session) {
      router.replace("/meetings");
    }
  }, [hydrated, router, session]);

  return (
    <AuthShell
      title="Sign in to your workspace"
      subtitle="Pick up your meeting queue, review transcript-backed action items, and keep the delivery thread moving."
      footer={
        <p>
          Need a workspace? <Link href="/sign-up">Create one</Link>
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
            const nextSession = await signIn(email, password);
            saveSession(nextSession);
            router.replace("/meetings");
          } catch (submitError) {
            setError(submitError instanceof Error ? submitError.message : "Sign-in failed");
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
          <span>Password</span>
          <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} required />
        </label>
        {error ? <p className="error-text">{error}</p> : null}
        <div className="form-actions">
          <button type="submit" className="primary-button" disabled={pending}>
            {pending ? <LoaderCircle size={16} className="spin" /> : <LogIn size={16} />}
            <span>{pending ? "Signing in" : "Sign in"}</span>
          </button>
        </div>
      </form>
    </AuthShell>
  );
}
