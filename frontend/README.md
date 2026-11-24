# Career Compass Web

Next.js App Router frontend for Career Compass. Supabase Auth owns account credentials and sessions; FastAPI owns application profiles and protected APIs.

## Local setup

1. Copy `.env.example` to `.env.local`.
2. Set `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY` using the Supabase project URL and public anon/publishable key. These `NEXT_PUBLIC_` values are intentionally browser-visible; never put service-role keys or secrets here.
3. Set `NEXT_PUBLIC_API_BASE_URL` to the FastAPI origin (for local development, `http://localhost:8000`, without `/api/v1`).
4. Configure the backend `CORS_ORIGINS` allowlist to include the frontend origin, normally `http://localhost:3000`.
5. Add the frontend origin and `/update-password` redirect to the Supabase Auth URL configuration.

Run the app and checks from this directory:

```sh
npm install
npm run dev
npm run test
npm run lint
npm run typecheck
npm run build
```

Open `http://localhost:3000`.

## Authentication flows

- `/signup` uses `supabase.auth.signUp()`. If email confirmation is required and Supabase returns no session, the UI asks the user to confirm email and then sign in.
- `/login` uses `supabase.auth.signInWithPassword()`.
- The shared auth provider persists sessions, detects auth callback URLs, subscribes to auth state changes, and enables SDK token refresh.
- Once a session is available, the frontend calls `GET /api/v1/profiles/me` with the access token; a 404 triggers authenticated `PUT /api/v1/profiles/me` to initialize the application profile.
- `/` is protected and redirects unauthenticated visitors to `/login`. API 401 responses sign the user out.
- `/forgot-password` sends a Supabase recovery email; `/update-password` uses the recovered session and `supabase.auth.updateUser()`.
- Sign-out calls `supabase.auth.signOut()` and returns to `/login`.

The frontend never reads or stores passwords outside Supabase Auth, and sends access tokens only in the `Authorization: Bearer` header to FastAPI.
