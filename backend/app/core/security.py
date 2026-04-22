import jwt
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from passlib.context import CryptContext

from app.exceptions import TokenExpiredError, TokenInvalidError


myctx = CryptContext(schemes=["argon2"], deprecated="auto")


class JWTManager:
    @staticmethod
    def create_token(payload: dict, secret_key: str, expires_minutes: int) -> tuple[str, str]:
        data_to_encode = payload.copy()
        now = datetime.now(timezone.utc)
        jti = uuid4().hex

        data_to_encode.update(
            {
                "exp": now + timedelta(minutes=expires_minutes),
                "iat": now,
                "jti": jti,
            }
        )

        return jwt.encode(data_to_encode, secret_key, algorithm="HS256"), jti

    @staticmethod
    def decode_token(token: str, secret_key: str) -> dict:
        try:
            return jwt.decode(token, secret_key, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError("Token is expired")
        except jwt.InvalidTokenError as e:
            raise TokenInvalidError(f"Invalid token: {e}")
