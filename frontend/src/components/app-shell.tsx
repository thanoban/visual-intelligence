"use client";

import Link from "next/link";
import { House, LogOut } from "lucide-react";
import { useRouter } from "next/navigation";

import { useSession } from "@/components/session-provider";

export function AppShell({
  title,
  subtitle,
  actions,
  children,
}: {
  title: string;
  subtitle: string;
  actions?: React.ReactNode;
  children: React.ReactNode;
}) {
  const router = useRouter();
  const { clearSession, session } = useSession();

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="topbar-inner">
          <div className="brand-block">
            <Link href="/meetings" className="brand-link">
              <span className="brand-mark">VS</span>
              <span className="brand-text">
                <strong>VisualSprint</strong>
                <span>{session?.workspace.name ?? "Workspace"}</span>
              </span>
            </Link>
          </div>
          <nav className="topbar-nav" aria-label="Primary">
            <Link href="/meetings" className="icon-link">
              <House size={16} />
              <span>Meetings</span>
            </Link>
          </nav>
          <div className="topbar-user">
            <div className="user-chip">
              <span>{session?.user.name ?? "Guest"}</span>
              <small>{session?.user.email ?? ""}</small>
            </div>
            <button
              type="button"
              className="icon-button"
              onClick={() => {
                clearSession();
                router.replace("/sign-in");
              }}
              aria-label="Sign out"
            >
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </header>
      <main className="page-shell">
        <section className="page-intro">
          <div>
            <p className="eyebrow">Meeting intelligence workspace</p>
            <h1>{title}</h1>
            <p className="lede">{subtitle}</p>
          </div>
          {actions ? <div className="page-actions">{actions}</div> : null}
        </section>
        {children}
      </main>
    </div>
  );
}
