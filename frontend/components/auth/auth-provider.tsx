"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import type { Session, SupabaseClient, User } from "@supabase/supabase-js";

import { ApiError, ensureMyProfile, type Profile } from "@/lib/api";
import {
  getSupabaseBrowserClient,
  isSupabaseConfigured,
} from "@/lib/supabase/browser";

type AuthContextValue = {
  user: User | null;
  session: Session | null;
  profile: Profile | null;
  isLoading: boolean;
  error: string | null;
  signOut: () => Promise<void>;
  refreshProfile: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [supabase] = useState<SupabaseClient | null>(() =>
    typeof window !== "undefined" && isSupabaseConfigured()
      ? getSupabaseBrowserClient()
      : null,
  );
  const [session, setSession] = useState<Session | null>(null);
  const [authLoading, setAuthLoading] = useState(() => isSupabaseConfigured());
  const [profile, setProfile] = useState<Profile | null>(null);
  const [error, setError] = useState<string | null>(() =>
    isSupabaseConfigured()
      ? null
      : "Authentication is not configured. Add the public Supabase URL and anon key to frontend environment variables.",
  );

  useEffect(() => {
    if (!isSupabaseConfigured()) return;

    const client = supabase;
    if (!client) return;
    let active = true;
    let receivedInitialAuthEvent = false;

    const {
      data: { subscription },
    } = client.auth.onAuthStateChange((_event, nextSession) => {
      receivedInitialAuthEvent = true;
      if (active) {
        setSession(nextSession);
        if (!nextSession) setProfile(null);
        setAuthLoading(false);
        setError(null);
      }
    });

    void client.auth.getSession().then(({ data, error: sessionError }) => {
      if (!active || receivedInitialAuthEvent) return;
      if (sessionError) setError(sessionError.message);
      setSession(data.session);
      setAuthLoading(false);
    });

    return () => {
      active = false;
      subscription.unsubscribe();
    };
  }, [supabase]);

  useEffect(() => {
    if (!session || !supabase) {
      return;
    }
    if (profile?.id === session.user.id) return;

    let active = true;

    void ensureMyProfile(session.access_token, session.user.id)
      .then((currentProfile) => {
        if (active) setProfile(currentProfile);
      })
      .catch(async (profileError: unknown) => {
        if (!active) return;
        if (profileError instanceof ApiError && profileError.status === 401) {
          await supabase.auth.signOut();
          setError("Your session has expired. Please sign in again.");
          return;
        }
        setError(
          profileError instanceof Error
            ? profileError.message
            : "Could not load your Career Compass profile.",
        );
      });

    return () => {
      active = false;
    };
  }, [profile?.id, session, supabase]);

  const signOut = useCallback(async () => {
    if (!supabase) return;
    const { error: signOutError } = await supabase.auth.signOut();
    if (signOutError) throw signOutError;
    setProfile(null);
  }, [supabase]);

  const refreshProfile = useCallback(async () => {
    if (!session) return;
    try {
      setProfile(await ensureMyProfile(session.access_token, session.user.id));
      setError(null);
    } catch (profileError) {
      setError(
        profileError instanceof Error
          ? profileError.message
          : "Could not refresh your profile.",
      );
      throw profileError;
    }
  }, [session]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user: session?.user ?? null,
      session,
      profile,
      isLoading:
        authLoading ||
        Boolean(session && profile?.id !== session.user.id && !error),
      error,
      signOut,
      refreshProfile,
    }),
    [authLoading, error, profile, refreshProfile, session, signOut],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider.");
  }
  return context;
}
