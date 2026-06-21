"""Web-console authentication (username/password + TOTP-2FA).

A thin auth surface for the REST console: an `auth.app_user` table (its own `auth` schema), argon2
password hashing, a signed session JWT carried in an httpOnly `kr_session` cookie, and TOTP-based
two-factor enrolment/verification. The API routers (`app/api/v1/auth.py`) wrap these primitives;
`app/auth/deps.py` exposes the `get_current_user` dependency the runs API depends on.
"""
