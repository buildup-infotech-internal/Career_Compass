export type Profile = {
  id: string;
  full_name: string | null;
  phone: string | null;
  location: string | null;
  education: Array<Record<string, unknown>>;
  experience: Array<Record<string, unknown>>;
  account_role: "learner" | "admin";
};

type ApiEnvelope<T> = {
  success: boolean;
  message: string;
  data?: T;
  errors?: unknown[];
};

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly details: unknown[] = [],
  ) {
    super(message);
    this.name = "ApiError";
  }
}

const profileInitializationRequests = new Map<string, Promise<Profile>>();

function getApiBaseUrl(): string {
  return (
    process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"
  ).replace(/\/$/, "");
}

export async function apiRequest<T>(
  path: string,
  accessToken: string,
  init: RequestInit = {},
): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  headers.set("Content-Type", "application/json");
  headers.set("Authorization", `Bearer ${accessToken}`);

  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    ...init,
    headers,
  });

  let payload: ApiEnvelope<T>;
  try {
    payload = (await response.json()) as ApiEnvelope<T>;
  } catch {
    throw new ApiError(
      "The API returned an unreadable response.",
      response.status,
    );
  }

  if (!response.ok || !payload.success) {
    throw new ApiError(
      payload.message || "The request could not be completed.",
      response.status,
      payload.errors,
    );
  }

  return payload.data as T;
}

export function getMyProfile(accessToken: string): Promise<Profile> {
  return apiRequest<Profile>("/api/v1/profiles/me", accessToken);
}

export function ensureMyProfile(
  accessToken: string,
  userId: string = accessToken,
): Promise<Profile> {
  const pendingRequest = profileInitializationRequests.get(userId);
  if (pendingRequest) return pendingRequest;

  const initialization = (async () => {
    try {
      return await getMyProfile(accessToken);
    } catch (error) {
      if (!(error instanceof ApiError) || error.status !== 404) {
        throw error;
      }
    }

    return apiRequest<Profile>("/api/v1/profiles/me", accessToken, {
      method: "PUT",
      body: JSON.stringify({}),
    });
  })();

  const sharedRequest = initialization.finally(() => {
    profileInitializationRequests.delete(userId);
  });
  profileInitializationRequests.set(userId, sharedRequest);
  return sharedRequest;
}
