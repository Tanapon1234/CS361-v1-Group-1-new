import { NextResponse, type NextRequest } from 'next/server';

import { cognitoEnabled, refresh } from '@/lib/auth/cognito';
import {
  ID_TOKEN_COOKIE,
  REFRESH_TOKEN_COOKIE,
  idTokenCookie,
  isFresh,
} from '@/lib/auth/session';

/**
 * /manage needs a signed-in user (Cognito mode). A fresh ID token passes; an expiring one is
 * refreshed here (pages cannot set cookies while rendering); no session goes to /login.
 * This is only the optimistic check: the backend verifies the token on every call.
 */
export async function proxy(request: NextRequest) {
  if (!cognitoEnabled()) return NextResponse.next();

  const idToken = request.cookies.get(ID_TOKEN_COOKIE)?.value;
  if (isFresh(idToken)) return NextResponse.next();

  const refreshToken = request.cookies.get(REFRESH_TOKEN_COOKIE)?.value;
  const tokens = refreshToken ? await refresh(refreshToken) : null;
  if (!tokens) {
    const login = new URL('/login', request.url);
    login.searchParams.set('next', request.nextUrl.pathname + request.nextUrl.search);
    const response = NextResponse.redirect(login);
    response.cookies.delete(ID_TOKEN_COOKIE);
    response.cookies.delete(REFRESH_TOKEN_COOKIE);
    return response;
  }

  // The page rendering now must see the new token too, not only the browser
  request.cookies.set(ID_TOKEN_COOKIE, tokens.idToken);
  const response = NextResponse.next({ request: { headers: request.headers } });
  response.cookies.set(...idTokenCookie(tokens.idToken, tokens.expiresIn));
  return response;
}

export const config = {
  matcher: ['/manage/:path*'],
};
