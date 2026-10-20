'use server';

import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';

import { revoke, setNewPassword, signIn, type SignInResult, type Tokens } from '@/lib/auth/cognito';
import {
  ID_TOKEN_COOKIE,
  REFRESH_TOKEN_COOKIE,
  idTokenCookie,
  refreshTokenCookie,
} from '@/lib/auth/session';

export type LoginState =
  | null
  | { step: 'password'; email: string; error: string }
  | { step: 'new-password'; email: string; session: string; error: string | null };

/** Only same-site paths, so `next` cannot send the user to another site */
function safeNext(value: FormDataEntryValue | null): string {
  const next = typeof value === 'string' ? value : '';
  return next.startsWith('/') && !next.startsWith('//') ? next : '/manage';
}

async function startSession(tokens: Tokens, next: string): Promise<never> {
  const jar = await cookies();
  jar.set(...idTokenCookie(tokens.idToken, tokens.expiresIn));
  if (tokens.refreshToken) jar.set(...refreshTokenCookie(tokens.refreshToken));
  redirect(next);
}

async function handle(result: SignInResult, email: string, next: string): Promise<LoginState> {
  if (result.kind === 'signed-in') return startSession(result.tokens, next);
  if (result.kind === 'new-password') {
    return { step: 'new-password', email, session: result.session, error: null };
  }
  return { step: 'password', email, error: result.message };
}

export async function login(_: LoginState, form: FormData): Promise<LoginState> {
  const email = String(form.get('email') ?? '').trim();
  const password = String(form.get('password') ?? '');
  if (!email || !password) return { step: 'password', email, error: 'กรอกอีเมลและรหัสผ่าน' };
  return handle(await signIn(email, password), email, safeNext(form.get('next')));
}

export async function chooseNewPassword(state: LoginState, form: FormData): Promise<LoginState> {
  if (state?.step !== 'new-password') return state;
  const password = String(form.get('new_password') ?? '');
  if (password !== String(form.get('confirm_password') ?? '')) {
    return { ...state, error: 'รหัสผ่านทั้งสองช่องไม่ตรงกัน' };
  }
  const result = await setNewPassword(state.email, password, state.session);
  if (result.kind === 'error') return { ...state, error: result.message };
  return handle(result, state.email, safeNext(form.get('next')));
}

export async function logout() {
  const jar = await cookies();
  const refreshToken = jar.get(REFRESH_TOKEN_COOKIE)?.value;
  if (refreshToken) await revoke(refreshToken);
  jar.delete(ID_TOKEN_COOKIE);
  jar.delete(REFRESH_TOKEN_COOKIE);
  redirect('/login');
}
