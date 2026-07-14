# 11 - Auth, Workspace, and Invites

This guide explains how users enter the system, how tenant boundaries are enforced, and how workspace membership works.

## 1. Feature scope

The auth and workspace layer currently covers:

- sign up
- sign in
- persistent browser session
- session refresh
- workspace ownership and member roles
- invite creation
- invite acceptance
- workspace settings
- workspace member and pending-invite visibility

Relevant backend files:

- `backend/app/api/routes/auth.py`
- `backend/app/api/routes/workspace.py`
- `backend/app/security.py`
- `backend/app/dependencies.py`
- `backend/app/models/entities.py`

Relevant frontend files:

- `frontend/src/components/session-provider.tsx`
- `frontend/src/app/sign-in/page.tsx`
- `frontend/src/app/sign-up/page.tsx`
- `frontend/src/app/invite/page.tsx`
- `frontend/src/app/settings/page.tsx`
- `frontend/src/lib/api.ts`
- `frontend/src/lib/types.ts`

## 2. Sign-up flow

The sign-up route lives in `auth.py` as `sign_up(...)`.

What it does:

1. normalizes the email with `_normalize_email()`
2. checks whether a user already exists
3. creates a new `Workspace`
4. creates a new `User` with role `owner`
5. hashes the password with `hash_password(...)`
6. commits both records
7. returns an authenticated session response immediately

Why this is useful:

- the first user is always the workspace owner
- there is no separate workspace-creation wizard
- the frontend can move straight into the product after account creation

## 3. Sign-in flow

The sign-in route:

1. looks up the user by normalized email
2. verifies the password with `verify_password(...)`
3. refreshes the `workspace` relationship
4. returns a fresh bearer token plus user and workspace info

The response model is `AuthSessionResponse`, which intentionally includes:

- the bearer token
- the user summary
- the workspace summary

That keeps the frontend from needing a second request before it can render the authenticated shell.

## 4. Password hashing method

Passwords are not stored directly. The repo uses:

- `hashlib.pbkdf2_hmac("sha256", ...)`
- a random 16-byte salt
- a high iteration count (`100_000`)

The resulting hash string is stored as:

`iterations$salt_hex$digest_hex`

Why this method matters:

- PBKDF2 slows down brute-force attacks
- per-user salts stop rainbow-table reuse
- verification uses `hmac.compare_digest(...)`, which avoids timing leaks better than plain string comparison

## 5. Access token method

This project does not use a JWT library yet. Instead it uses a custom HMAC-signed token format in `security.py`.

### Token creation

`create_access_token(...)` builds a JSON payload containing:

- `user_id`
- `workspace_id`
- `exp`

Then it:

1. serializes the JSON deterministically
2. base64-url encodes the payload
3. signs the payload token with HMAC-SHA256 using `app_secret_key`
4. returns `payload.signature`

### Token verification

`decode_access_token(...)`:

1. splits the token into payload and signature
2. recalculates the expected signature
3. compares signatures with `hmac.compare_digest(...)`
4. decodes the JSON payload
5. checks expiry

This is simpler than full JWT support and works well for the current milestone.

## 6. Why `workspace_id` is inside the token

Including `workspace_id` in the token lets the backend reject tokens that do not match the current stored user/workspace relationship.

`get_current_user(...)` in `dependencies.py` loads the user record and verifies:

- the user still exists
- the user's `workspace_id` still matches the token payload

That makes the token more than an identity proof. It is also a tenant-bound access proof.

## 7. Invite creation flow

Invite creation currently lives in `auth.py` as `create_invite(...)`.

Behavior:

1. only owners are allowed to invite
2. the email is normalized
3. existing users are rejected
4. duplicate pending invites for the same workspace and email are rejected
5. a unique token is generated with `secrets.token_urlsafe(32)`
6. the invite expires in 7 days

Important detail:

there is no outbound email delivery yet. The system creates the invite record and exposes the token, and the frontend settings page currently lets owners copy the acceptance link manually.

## 8. Invite acceptance flow

Invite acceptance happens in `accept_invite(...)`.

The route verifies:

- the token exists
- the invite is still pending
- the invite is not expired
- the email in the request matches the invite email
- the email is not already registered

Then it:

1. creates a new member user
2. marks the invite as accepted
3. stamps `accepted_at`
4. returns a full authenticated session

This is why the frontend `/invite` page can function as a direct onboarding entry point.

## 9. Workspace settings flow

Workspace settings currently store lightweight operational preferences:

- default language hint
- default Slack channel
- whether Slack auto-post should happen once the notify integration exists

The settings route intentionally keeps the structure generic by storing values in `Workspace.settings`, a JSON field. That makes the model easy to evolve without adding a new SQL column for every preference.

## 10. Workspace members and invites

`GET /workspace/members` returns:

- a sorted member list
- a sorted invite list

The current backend sorts members so the owner appears first, and sorts invites so pending invites appear before already accepted ones.

That route powers the settings-page roster and pending invite management UI.

## 11. Frontend session architecture

The most important frontend auth file is `session-provider.tsx`.

### What it owns

- loading the session from `localStorage`
- refreshing it against `/auth/session`
- saving new sessions after sign-in, sign-up, or invite acceptance
- clearing expired or invalid sessions

### Why `hydrated` exists

The browser cannot read `localStorage` during the server render. The `hydrated` flag stops pages from making routing decisions until the browser-side session state is ready.

Without that flag, you get redirect flicker and hydration mismatch behavior.

## 12. Sign-in and sign-up pages

The sign-in and sign-up pages are intentionally thin:

- collect form state
- call `signIn(...)` or `signUp(...)`
- save the returned session
- redirect to `/meetings`

This is a consistent pattern in the frontend: pages own interaction state, while `lib/api.ts` owns request details.

## 13. Invite acceptance page

`frontend/src/app/invite/page.tsx` is worth reading carefully because it contains a subtle App Router rule.

It uses `useSearchParams()` to read:

- `token`
- `email`

Because `useSearchParams()` is client-side stateful routing data, the page is wrapped in `Suspense`. That is required by Next.js for this route to build cleanly.

The page:

1. validates that a token and linked email are present
2. shows a simple acceptance form
3. posts to `/auth/invites/accept`
4. saves the returned session
5. redirects to `/meetings`

## 14. Tenant security model

This project uses a layered workspace boundary:

### Layer 1: token verification

The token must be valid and unexpired.

### Layer 2: user existence

The `user_id` in the token must map to a real user.

### Layer 3: workspace consistency

The token's `workspace_id` must still match the stored user row.

### Layer 4: route-level scoped queries

Meeting and workspace routes do not trust client-provided ids alone. They query records within the current workspace.

This is why cross-workspace access tests are so important in the suite.

## 15. Extension points you should notice

Several future features will naturally build on this layer:

- Google sign-in can return the same `AuthSessionResponse` shape
- audit logs can expand from draft actions to membership and settings changes
- SSO can replace password creation while leaving workspace scoping intact
- email delivery can wrap around the existing invite token flow

The repo is already shaped for those upgrades.
