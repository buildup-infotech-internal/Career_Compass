import Link from "next/link";
import type { ReactNode } from "react";

export function AuthCard({
  eyebrow,
  title,
  description,
  children,
  footer,
}: {
  eyebrow: string;
  title: string;
  description: string;
  children: ReactNode;
  footer: ReactNode;
}) {
  return (
    <main className="auth-shell">
      <section className="auth-aside">
        <Link className="brand-lockup" href="/">
          <span className="brand-mark">C</span>
          <span>Career Compass</span>
        </Link>
        <div className="aside-copy">
          <p className="eyebrow">A clearer way forward</p>
          <h1>Build a career that feels like yours.</h1>
          <p>
            Turn your strengths into a practical next step—with guidance that
            keeps your goals in view.
          </p>
        </div>
        <div className="aside-note">
          <span className="note-dot" /> Your next chapter starts here
        </div>
        <div className="aside-orbit orbit-one" />
        <div className="aside-orbit orbit-two" />
      </section>

      <section className="auth-main">
        <div className="auth-panel">
          <p className="eyebrow">{eyebrow}</p>
          <h2>{title}</h2>
          <p className="auth-description">{description}</p>
          {children}
          <div className="auth-footer">{footer}</div>
        </div>
        <p className="legal-note">
          By continuing, you agree to use Career Compass responsibly.
        </p>
      </section>
    </main>
  );
}
