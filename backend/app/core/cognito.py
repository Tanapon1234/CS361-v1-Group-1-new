"""Verify Amazon Cognito ID tokens (RS256) issued to our app client."""

import json
from typing import Any

import jwt

from app.core.exceptions import UnauthorizedError


class CognitoTokenVerifier:
    def __init__(self, *, issuer: str, client_id: str, jwks_json: str = "") -> None:
        self.issuer = issuer
        self.client_id = client_id
        # Keys given up front (a Lambda without internet access), or fetched and cached
        self._keys = jwt.PyJWKSet.from_dict(json.loads(jwks_json)) if jwks_json else None
        self._client = None if jwks_json else jwt.PyJWKClient(f"{issuer}/.well-known/jwks.json")

    def verify(self, token: str) -> dict[str, Any]:
        """The token's claims; UnauthorizedError if it is not a valid, current ID token."""
        try:
            key = self._signing_key(jwt.get_unverified_header(token).get("kid"))
            claims = jwt.decode(
                token,
                key,
                algorithms=["RS256"],
                audience=self.client_id,
                issuer=self.issuer,
                options={"require": ["exp", "iat", "sub", "aud", "iss"]},
            )
        except (jwt.PyJWTError, KeyError) as exc:
            raise UnauthorizedError("Invalid or expired sign-in token") from exc
        if claims.get("token_use") != "id":
            raise UnauthorizedError("Send the Cognito ID token, not the access token")
        return claims

    def _signing_key(self, kid: str | None) -> Any:
        if self._keys is not None:
            return self._keys[kid].key
        assert self._client is not None
        return self._client.get_signing_key(kid).key
