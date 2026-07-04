import Link from "next/link";

export function AuthShell({
  title,
  subtitle,
  footer,
  children,
}: {
  title: string;
  subtitle: string;
  footer: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <main className="auth-page">
      <section className="auth-hero">
        <div className="auth-copy">
          <p className="eyebrow">VisualSprint</p>
          <h1>{title}</h1>
          <p className="lede">{subtitle}</p>
          <div className="auth-proof">
            <span>Multilingual transcripts</span>
            <span>Evidence-backed action items</span>
            <span>Cited meeting answers</span>
          </div>
        </div>
        <div className="auth-panel">
          {children}
          <div className="auth-footer">{footer}</div>
        </div>
      </section>
      <footer className="site-footer">
        <Link href="/sign-in">Sign in</Link>
        <Link href="/sign-up">Create workspace</Link>
      </footer>
    </main>
  );
}
