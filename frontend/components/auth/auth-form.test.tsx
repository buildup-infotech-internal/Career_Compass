import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AuthForm } from "@/components/auth/auth-form";
import {
  PasswordRecoveryRequest,
  UpdatePasswordForm,
} from "@/components/auth/password-recovery";

const {
  replace,
  signUp,
  signInWithPassword,
  resetPasswordForEmail,
  updateUser,
  useAuthMock,
} = vi.hoisted(() => ({
  replace: vi.fn(),
  signUp: vi.fn(),
  signInWithPassword: vi.fn(),
  resetPasswordForEmail: vi.fn(),
  updateUser: vi.fn(),
  useAuthMock: vi.fn(),
}));

vi.mock("next/navigation", () => ({ useRouter: () => ({ replace }) }));
vi.mock("@/components/auth/auth-provider", () => ({
  useAuth: useAuthMock,
}));
vi.mock("@/lib/supabase/browser", () => ({
  getSupabaseBrowserClient: () => ({
    auth: { signUp, signInWithPassword, resetPasswordForEmail, updateUser },
  }),
}));

beforeEach(() => {
  vi.clearAllMocks();
  useAuthMock.mockReturnValue({ user: null, session: null, isLoading: false });
});

describe("AuthForm", () => {
  it("explains confirmation-required signup when Supabase returns no session", async () => {
    signUp.mockResolvedValue({ data: { session: null }, error: null });
    render(<AuthForm mode="signup" />);

    fireEvent.change(screen.getByLabelText("Email address"), {
      target: { value: "learner@example.test" },
    });
    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "a-secure-password" },
    });
    fireEvent.click(screen.getByRole("button", { name: /create account/i }));

    expect(await screen.findByRole("status")).toHaveTextContent(
      "Check your email to confirm",
    );
    expect(replace).not.toHaveBeenCalled();
  });

  it("reports login errors returned by Supabase", async () => {
    signInWithPassword.mockResolvedValue({
      error: new Error("Invalid login credentials"),
    });
    render(<AuthForm mode="login" />);

    fireEvent.change(screen.getByLabelText("Email address"), {
      target: { value: "learner@example.test" },
    });
    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "incorrect-password" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await waitFor(() =>
      expect(screen.getByRole("alert")).toHaveTextContent(
        "Invalid login credentials",
      ),
    );
  });

  it("requests a recovery email with the password-update callback URL", async () => {
    resetPasswordForEmail.mockResolvedValue({ error: null });
    render(<PasswordRecoveryRequest />);

    fireEvent.change(screen.getByLabelText("Email address"), {
      target: { value: "learner@example.test" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: /send recovery link/i }),
    );

    expect(await screen.findByRole("status")).toHaveTextContent(
      "If an account exists",
    );
    expect(resetPasswordForEmail).toHaveBeenCalledWith("learner@example.test", {
      redirectTo: `${window.location.origin}/update-password`,
    });
  });

  it("updates the password only when a recovery session exists", async () => {
    useAuthMock.mockReturnValue({
      user: null,
      session: { access_token: "recovery-session" },
      isLoading: false,
    });
    updateUser.mockResolvedValue({ error: null });
    render(<UpdatePasswordForm />);

    fireEvent.change(screen.getByLabelText("New password"), {
      target: { value: "a-new-secure-password" },
    });
    fireEvent.click(screen.getByRole("button", { name: /update password/i }));

    expect(await screen.findByRole("status")).toHaveTextContent(
      "Password updated",
    );
    expect(updateUser).toHaveBeenCalledWith({
      password: "a-new-secure-password",
    });
  });
});
