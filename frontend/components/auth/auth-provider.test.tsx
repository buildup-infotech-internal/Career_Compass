import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AuthProvider, useAuth } from "@/components/auth/auth-provider";

const session = {
  access_token: "test-access-token",
  user: { id: "user-123", email: "learner@example.test" },
};
const profile = {
  id: "user-123",
  full_name: "Jordan Lee",
  phone: null,
  location: null,
  education: [],
  experience: [],
  account_role: "learner" as const,
};

const { getSessionMock, subscribeMock, unsubscribeMock, ensureProfileMock } =
  vi.hoisted(() => ({
    getSessionMock: vi.fn(),
    subscribeMock: vi.fn(),
    unsubscribeMock: vi.fn(),
    ensureProfileMock: vi.fn(),
  }));

vi.mock("@/lib/supabase/browser", () => ({
  isSupabaseConfigured: () => true,
  getSupabaseBrowserClient: () => ({
    auth: {
      onAuthStateChange: (callback: unknown) => {
        subscribeMock(callback);
        return { data: { subscription: { unsubscribe: unsubscribeMock } } };
      },
      getSession: getSessionMock,
      signOut: vi.fn(),
    },
  }),
}));
vi.mock("@/lib/api", () => ({
  ApiError: class ApiError extends Error {
    status = 500;
  },
  ensureMyProfile: ensureProfileMock,
}));

function AuthStateProbe() {
  const { user, profile: currentProfile, isLoading } = useAuth();
  return (
    <div>
      <span>{isLoading ? "loading" : "ready"}</span>
      <span>{user?.id ?? "signed-out"}</span>
      <span>{currentProfile?.full_name ?? "no-profile"}</span>
    </div>
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  getSessionMock.mockResolvedValue({ data: { session }, error: null });
  ensureProfileMock.mockResolvedValue(profile);
});

describe("AuthProvider", () => {
  it("loads a persisted SDK session and initializes the matching app profile", async () => {
    render(
      <AuthProvider>
        <AuthStateProbe />
      </AuthProvider>,
    );

    await waitFor(() =>
      expect(screen.getByText("Jordan Lee")).toBeInTheDocument(),
    );

    expect(screen.getByText("user-123")).toBeInTheDocument();
    expect(screen.getByText("ready")).toBeInTheDocument();
    expect(ensureProfileMock).toHaveBeenCalledWith(
      "test-access-token",
      "user-123",
    );
    expect(subscribeMock).toHaveBeenCalledTimes(1);
  });
});
