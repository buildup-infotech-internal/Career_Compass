"use client";

import { useEffect, useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { useAuth } from "@/components/auth/auth-provider";
import { getSupabaseBrowserClient } from "@/lib/supabase/browser";

type AuthFormMode = "login" | "signup";

export function AuthForm({ mode }: { mode: AuthFormMode }) {
  const router = useRouter();
  const { user, isLoading } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoading && user) router.replace("/");
  }, [isLoading, router, user]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    setNotice(null);

    try {
      const supabase = getSupabaseBrowserClient();
      if (mode === "signup") {
        const { data, error: signupError } = await supabase.auth.signUp({
          email,
          password,
          options: {
            emailRedirectTo: `${window.location.origin}/`,
          },
        });

        if (signupError) throw signupError;
        if (!data.session) {
          setNotice(
            "Your account was created. Check your email to confirm your address, then sign in to finish setting up your profile.",
          );
          return;
        }
        router.replace("/");
      } else {
        const { error: loginError } = await supabase.auth.signInWithPassword({
          email,
          password,
        });
        if (loginError) throw loginError;
        router.replace("/");
      }
    } catch (authError) {
      setError(
        authError instanceof Error
          ? authError.message
          : "Authentication could not be completed.",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="auth-form" onSubmit={handleSubmit}>
      <label className="field-label" htmlFor={`${mode}-email`}>
        Email address
      </label>
      <input
        autoComplete="email"
        className="text-input"
        id={`${mode}-email`}
        onChange={(event) => setEmail(event.target.value)}
        placeholder="you@example.com"
        required
        type="email"
        value={email}
      />

      <div className="field-heading">
        <label className="field-label" htmlFor={`${mode}-password`}>
          Password
        </label>
        {mode === "login" && (
          <Link className="text-link" href="/forgot-password">
            Forgot password?
          </Link>
        )}
      </div>
      <input
        autoComplete={mode === "signup" ? "new-password" : "current-password"}
        className="text-input"
        id={`${mode}-password`}
        minLength={8}
        onChange={(event) => setPassword(event.target.value)}
        placeholder="At least 8 characters"
        required
        type="password"
        value={password}
      />

      {error && (
        <p className="form-message error-message" role="alert">
          {error}
        </p>
      )}
      {notice && (
        <p className="form-message success-message" role="status">
          {notice}
        </p>
      )}

      <button className="primary-button" disabled={busy} type="submit">
        {busy
          ? "Please wait…"
          : mode === "signup"
            ? "Create account"
            : "Sign in"}
        <span aria-hidden="true">↗</span>
      </button>
    </form>
  );
}
