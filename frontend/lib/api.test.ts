import { afterEach, describe, expect, it, vi } from "vitest";

import { ensureMyProfile } from "@/lib/api";

const profile = {
  id: "user-uuid",
  full_name: null,
  phone: null,
  location: null,
  education: [],
  experience: [],
  account_role: "learner" as const,
};

function apiResponse(status: number, body: object): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("ensureMyProfile", () => {
  it("returns the profile when it already exists", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(
        apiResponse(200, { success: true, message: "ok", data: profile }),
      );
    vi.stubGlobal("fetch", fetchMock);

    await expect(ensureMyProfile("access-token")).resolves.toEqual(profile);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const request = fetchMock.mock.calls[0][1] as RequestInit;
    expect(new Headers(request.headers).get("Authorization")).toBe(
      "Bearer access-token",
    );
  });

  it("initializes a missing profile with an authenticated PUT", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        apiResponse(404, {
          success: false,
          message: "Profile not found",
          errors: [],
        }),
      )
      .mockResolvedValueOnce(
        apiResponse(200, { success: true, message: "created", data: profile }),
      );
    vi.stubGlobal("fetch", fetchMock);

    await expect(ensureMyProfile("session-access-token")).resolves.toEqual(
      profile,
    );
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(fetchMock.mock.calls[1][0]).toContain("/api/v1/profiles/me");
    const request = fetchMock.mock.calls[1][1] as RequestInit;
    expect(request.method).toBe("PUT");
    expect(request.body).toBe("{}");
    expect(new Headers(request.headers).get("Authorization")).toBe(
      "Bearer session-access-token",
    );
  });

  it("does not initialize on errors other than profile-not-found", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      apiResponse(500, {
        success: false,
        message: "Database unavailable",
        errors: [],
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(ensureMyProfile("access-token")).rejects.toMatchObject({
      status: 500,
    });
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("deduplicates concurrent initialization requests for the same user", async () => {
    let resolveProfile!: (value: Response) => void;
    const fetchMock = vi.fn().mockImplementation(
      () =>
        new Promise<Response>((resolve) => {
          resolveProfile = resolve;
        }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const first = ensureMyProfile("access-token", "same-user");
    const second = ensureMyProfile("access-token", "same-user");

    expect(fetchMock).toHaveBeenCalledTimes(1);
    resolveProfile(
      apiResponse(200, { success: true, message: "ok", data: profile }),
    );
    await expect(Promise.all([first, second])).resolves.toEqual([
      profile,
      profile,
    ]);
  });
});
