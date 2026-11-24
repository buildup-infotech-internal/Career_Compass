import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const { createClientMock } = vi.hoisted(() => ({
  createClientMock: vi.fn(),
}));

vi.mock("@supabase/supabase-js", () => ({
  createClient: createClientMock,
}));

beforeEach(() => {
  vi.resetModules();
  createClientMock.mockReset();
  process.env.NEXT_PUBLIC_SUPABASE_URL = "https://project.example.supabase.co";
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY = "public-test-key";
});

afterEach(() => {
  delete process.env.NEXT_PUBLIC_SUPABASE_URL;
  delete process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
});

describe("browser Supabase client", () => {
  it("creates one persistent client with automatic refresh and URL callback detection", async () => {
    const client = { auth: {} };
    createClientMock.mockReturnValue(client);
    const { getSupabaseBrowserClient } = await import("@/lib/supabase/browser");

    expect(getSupabaseBrowserClient()).toBe(client);
    expect(getSupabaseBrowserClient()).toBe(client);
    expect(createClientMock).toHaveBeenCalledTimes(1);
    expect(createClientMock).toHaveBeenCalledWith(
      "https://project.example.supabase.co",
      "public-test-key",
      {
        auth: {
          autoRefreshToken: true,
          detectSessionInUrl: true,
          persistSession: true,
        },
      },
    );
  });
});
