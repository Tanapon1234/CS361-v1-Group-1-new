/**
 * Amazon Cognito user pool API, called from the Next.js server only (no SDK needed: the
 * app client has no secret, so these calls are unsigned). Used by the login Server Actions
 * and by proxy.ts to refresh an expired ID token.
 */

export const COGNITO_REGION = process.env.COGNITO_REGION || 'ap-southeast-1';
export const COGNITO_CLIENT_ID = process.env.COGNITO_CLIENT_ID ?? '';
/** Override only for a local stand-in (LocalStack, tests); the default is the AWS endpoint */
const COGNITO_ENDPOINT =
  process.env.COGNITO_ENDPOINT || `https://cognito-idp.${COGNITO_REGION}.amazonaws.com/`;

/** Sign-in with Cognito is on when the app client is configured; otherwise dev mode */
export const cognitoEnabled = () => COGNITO_CLIENT_ID !== '';

export interface Tokens {
  idToken: string;
  /** Absent when refreshing: the refresh token stays the same */
  refreshToken?: string;
  expiresIn: number;
}

export type SignInResult =
  | { kind: 'signed-in'; tokens: Tokens }
  | { kind: 'new-password'; session: string }
  | { kind: 'error'; message: string };

const MESSAGES: Record<string, string> = {
  NotAuthorizedException: 'อีเมลหรือรหัสผ่านไม่ถูกต้อง',
  UserNotFoundException: 'อีเมลหรือรหัสผ่านไม่ถูกต้อง',
  PasswordResetRequiredException: 'ต้องตั้งรหัสผ่านใหม่ กรุณาติดต่อเจ้าหน้าที่',
  UserNotConfirmedException: 'บัญชียังไม่ได้ยืนยัน กรุณาติดต่อเจ้าหน้าที่',
  InvalidPasswordException:
    'รหัสผ่านใหม่ไม่ตรงเงื่อนไข: อย่างน้อย 10 ตัว มีตัวพิมพ์เล็ก ตัวพิมพ์ใหญ่ และตัวเลข',
  TooManyRequestsException: 'ลองบ่อยเกินไป กรุณารอสักครู่',
  LimitExceededException: 'ลองบ่อยเกินไป กรุณารอสักครู่',
  CodeMismatchException: 'เซสชันหมดอายุ กรุณาเข้าสู่ระบบใหม่',
  ExpiredCodeException: 'เซสชันหมดอายุ กรุณาเข้าสู่ระบบใหม่',
};

/** The parts of Cognito's JSON responses this file reads */
interface CognitoPayload {
  __type?: string;
  ChallengeName?: string;
  Session?: string;
  AuthenticationResult?: { IdToken?: string; RefreshToken?: string; ExpiresIn?: number };
}

class CognitoError extends Error {
  constructor(readonly type: string, message: string) {
    super(message);
  }
}

async function call(target: string, body: Record<string, unknown>): Promise<CognitoPayload> {
  let response: Response;
  try {
    response = await fetch(COGNITO_ENDPOINT, {
      method: 'POST',
      cache: 'no-store',
      headers: {
        'Content-Type': 'application/x-amz-json-1.1',
        'X-Amz-Target': `AWSCognitoIdentityProviderService.${target}`,
      },
      body: JSON.stringify(body),
    });
  } catch {
    throw new CognitoError('NetworkError', 'เชื่อมต่อระบบยืนยันตัวตนไม่ได้');
  }
  const payload: CognitoPayload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const type = String(payload.__type ?? '').split('#').pop() ?? '';
    throw new CognitoError(type, MESSAGES[type] ?? 'เข้าสู่ระบบไม่สำเร็จ');
  }
  return payload;
}

function asResult(payload: CognitoPayload): SignInResult {
  if (payload.ChallengeName === 'NEW_PASSWORD_REQUIRED' && payload.Session) {
    return { kind: 'new-password', session: payload.Session };
  }
  const result = payload.AuthenticationResult;
  if (!result?.IdToken) return { kind: 'error', message: 'บัญชีนี้ต้องยืนยันตัวตนเพิ่ม ซึ่งระบบยังไม่รองรับ' };
  return {
    kind: 'signed-in',
    tokens: {
      idToken: result.IdToken,
      refreshToken: result.RefreshToken,
      expiresIn: result.ExpiresIn ?? 3600,
    },
  };
}

async function attempt(work: () => Promise<SignInResult>): Promise<SignInResult> {
  try {
    return await work();
  } catch (error) {
    if (error instanceof CognitoError) return { kind: 'error', message: error.message };
    throw error;
  }
}

export function signIn(email: string, password: string): Promise<SignInResult> {
  return attempt(async () =>
    asResult(
      await call('InitiateAuth', {
        AuthFlow: 'USER_PASSWORD_AUTH',
        ClientId: COGNITO_CLIENT_ID,
        AuthParameters: { USERNAME: email, PASSWORD: password },
      })
    )
  );
}

/** First sign-in of an account created with a temporary password */
export function setNewPassword(email: string, newPassword: string, session: string): Promise<SignInResult> {
  return attempt(async () =>
    asResult(
      await call('RespondToAuthChallenge', {
        ChallengeName: 'NEW_PASSWORD_REQUIRED',
        ClientId: COGNITO_CLIENT_ID,
        Session: session,
        ChallengeResponses: { USERNAME: email, NEW_PASSWORD: newPassword },
      })
    )
  );
}

/** A new ID token from the refresh token, or null if it is no longer valid */
export async function refresh(refreshToken: string): Promise<Tokens | null> {
  try {
    const result = asResult(
      await call('InitiateAuth', {
        AuthFlow: 'REFRESH_TOKEN_AUTH',
        ClientId: COGNITO_CLIENT_ID,
        AuthParameters: { REFRESH_TOKEN: refreshToken },
      })
    );
    return result.kind === 'signed-in' ? result.tokens : null;
  } catch (error) {
    if (error instanceof CognitoError) return null;
    throw error;
  }
}

/** Sign out everywhere this refresh token was used (the app client allows revocation) */
export async function revoke(refreshToken: string): Promise<void> {
  try {
    await call('RevokeToken', { Token: refreshToken, ClientId: COGNITO_CLIENT_ID });
  } catch {
    // Signing out locally still works; the token expires on its own
  }
}
