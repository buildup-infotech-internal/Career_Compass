"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { useAuth } from "@/components/auth/auth-provider";
import { getSupabaseBrowserClient } from "@/lib/supabase/browser";

export function PasswordRecoveryRequest() {
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sent, setSent] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const redirectTo = `${window.location.origin}/update-password`;
      const { error: resetError } =
        await getSupabaseBrowserClient().auth.resetPasswordForEmail(email, {
          redirectTo,
        });
      if (resetError) throw resetError;
      setSent(true);
    } catch (resetError) {
      setError(
        resetError instanceof Error
          ? resetError.message
          : "Could not send the recovery email.",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="auth-form" onSubmit={handleSubmit}>
      {sent ? (
        <p className="form-message success-message" role="status">
          If an account exists for that address, a password recovery link is on
          its way.
        </p>
      ) : (
        <>
          <label className="field-label" htmlFor="recovery-email">
            Email address
          </label>
          <input
            autoComplete="email"
            className="text-input"
            id="recovery-email"
            onChange={(event) => setEmail(event.target.value)}
            required
            type="email"
            value={email}
          />
          {error && (
            <p className="form-message error-message" role="alert">
              {error}
            </p>
          )}
          <button className="primary-button" disabled={busy} type="submit">
            {busy ? "Sending…" : "Send recovery link"}
            <span aria-hidden="true">↗</span>
          </button>
        </>
      )}
      <Link className="back-link" href="/login">
        ← Back to sign in
      </Link>
    </form>
  );
}

export function UpdatePasswordForm() {
  const router = useRouter();
  const { session, isLoading } = useAuth();
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [updated, setUpdated] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const { error: updateError } =
        await getSupabaseBrowserClient().auth.updateUser({
          password,
        });
      if (updateError) throw updateError;
      setUpdated(true);
      window.setTimeout(() => router.replace("/"), 1200);
    } catch (updateError) {
      setError(
        updateError instanceof Error
          ? updateError.message
          : "Could not update your password.",
      );
    } finally {
      setBusy(false);
    }
  }

  if (isLoading) {
    return (
      <p className="form-message" role="status">
        Checking recovery link…
      </p>
    );
  }

  if (!session) {
    return (
      <div>
        <p className="form-message error-message" role="alert">
          This recovery link is invalid or expired. Request a new one to
          continue.
        </p>
        <Link className="primary-button button-link" href="/forgot-password">
          Request a new link
        </Link>
      </div>
    );
  }

  if (updated) {
    return (
      <p className="form-message success-message" role="status">
        Password updated. Taking you to your workspace…
      </p>
    );
  }

  return (
    <form className="auth-form" onSubmit={handleSubmit}>
      <label className="field-label" htmlFor="new-password">
        New password
      </label>
      <input
        autoComplete="new-password"
        className="text-input"
        id="new-password"
        minLength={8}
        onChange={(event) => setPassword(event.target.value)}
        required
        type="password"
        value={password}
      />
      {error && (
        <p className="form-message error-message" role="alert">
          {error}
        </p>
      )}
      <button className="primary-button" disabled={busy} type="submit">
        {busy ? "Updating…" : "Update password"}
        <span aria-hidden="true">↗</span>
      </button>
    </form>
  );
}
