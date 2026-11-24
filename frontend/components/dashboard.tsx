"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { ProtectedPage } from "@/components/auth/protected-page";
import { useAuth } from "@/components/auth/auth-provider";

function DashboardContent() {
  const router = useRouter();
  const { user, profile, error, signOut } = useAuth();
  const [signingOut, setSigningOut] = useState(false);
  const firstName = profile?.full_name?.trim().split(/\s+/)[0] || "there";

  async function handleSignOut() {
    setSigningOut(true);
    try {
      await signOut();
      router.replace("/login");
    } finally {
      setSigningOut(false);
    }
  }

  return (
    <main className="dashboard-shell">
      <header className="dashboard-header">
        <Link className="brand-lockup" href="/">
          <span className="brand-mark">C</span>
          <span>Career Compass</span>
        </Link>
        <div className="header-actions">
          <span className="account-chip">
            <span className="avatar-dot">{firstName[0]?.toUpperCase()}</span>
            <span>{user?.email}</span>
          </span>
          <button
            className="quiet-button"
            disabled={signingOut}
            onClick={handleSignOut}
            type="button"
          >
            {signingOut ? "Signing out…" : "Sign out"}
          </button>
        </div>
      </header>

      <section className="welcome-card">
        <div className="welcome-copy">
          <p className="eyebrow">Your career workspace</p>
          <h1>Good to see you, {firstName}.</h1>
          <p>
            Your profile is ready. This is the starting point for your career
            exploration and next steps.
          </p>
        </div>
        <div className="compass-art" aria-hidden="true">
          <span className="compass-ring ring-outer" />
          <span className="compass-ring ring-inner" />
          <span className="compass-needle">✦</span>
        </div>
      </section>

      {error && (
        <p className="form-message error-message" role="alert">
          {error}
        </p>
      )}

      <section className="dashboard-grid" aria-label="Profile overview">
        <article className="info-card profile-card">
          <div className="card-heading">
            <div>
              <p className="eyebrow">Your profile</p>
              <h2>Personal details</h2>
            </div>
            <span className="card-icon">◎</span>
          </div>
          <dl className="profile-details">
            <div>
              <dt>Full name</dt>
              <dd>{profile?.full_name || "Not added yet"}</dd>
            </div>
            <div>
              <dt>Email</dt>
              <dd>{user?.email || "—"}</dd>
            </div>
            <div>
              <dt>Location</dt>
              <dd>{profile?.location || "Not added yet"}</dd>
            </div>
            <div>
              <dt>Account</dt>
              <dd className="role-value">
                {profile?.account_role || "learner"}
              </dd>
            </div>
          </dl>
          <p className="card-footnote">
            Your signed-in account is securely connected to your profile.
          </p>
        </article>

        <article className="info-card next-card">
          <p className="eyebrow">Coming into focus</p>
          <h2>Small steps make big shifts.</h2>
          <p>
            Career recommendations, skill insights, and learning plans will
            appear here as you build your compass.
          </p>
          <div className="progress-line">
            <span />
          </div>
          <p className="progress-caption">Your workspace is set up</p>
        </article>
      </section>
    </main>
  );
}

export function Dashboard() {
  return (
    <ProtectedPage>
      <DashboardContent />
    </ProtectedPage>
  );
}
