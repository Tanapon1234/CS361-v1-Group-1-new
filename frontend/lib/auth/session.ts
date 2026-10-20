/**
 * Where the sign-in lives: httpOnly cookies the browser cannot read.
 * - Cognito: the ID token (sent to the backend as a Bearer token) and the refresh token
 * - Dev mode (no COGNITO_CLIENT_ID): the lecturer and roles picked on /manage/switch-user,
 *   sent as X-Lecturer-Id / X-Dev-Roles (the backend ignores them in prod)
 * No 'server-only' import: proxy.ts uses the cookie helpers too.
 */

export const ID_TOKEN_COOKIE = 'cs361_id_token';
export const REFRESH_TOKEN_COOKIE = 'cs361_refresh_token';
export const DEV_LECTURER_COOKIE = 'cs361_lecturer_id';
export const DEV_ROLES_COOKIE = 'cs361_dev_roles';

/** Refresh this long before the ID token expires */
const EXPIRY_MARGIN_SECONDS = 60;
const REFRESH_TOKEN_MAX_AGE = 12 * 60 * 60;

export interface CookieOptions {
  httpOnly: boolean;
  sameSite: 'lax';
  secure: boolean;
  path: string;
  maxAge: number;
}

export function cookieOptions(maxAge: number): CookieOptions {
  return {
    httpOnly: true,
    sameSite: 'lax',
    secure: process.env.NODE_ENV === 'production',
    path: '/',
    maxAge,
  };
}

export const idTokenCookie = (idToken: string, expiresIn: number) =>
  [ID_TOKEN_COOKIE, idToken, cookieOptions(expiresIn)] as const;
export const refreshTokenCookie = (refreshToken: string) =>
  [REFRESH_TOKEN_COOKIE, refreshToken, cookieOptions(REFRESH_TOKEN_MAX_AGE)] as const;

/** Seconds left on a JWT, from its `exp` claim (not verified here: the backend verifies) */
export function secondsLeft(token: string | undefined): number {
  if (!token) return 0;
  try {
    const payload = JSON.parse(Buffer.from(token.split('.')[1], 'base64url').toString('utf8'));
    return Number(payload.exp) - Math.floor(Date.now() / 1000);
  } catch {
    return 0;
  }
}

export const isFresh = (token: string | undefined) => secondsLeft(token) > EXPIRY_MARGIN_SECONDS;
