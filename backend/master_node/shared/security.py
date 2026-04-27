import hashlib
import hmac
import time


def build_chunk_signature(chunk_id: int, exp: int, secret: str) -> str:
    payload = f"{chunk_id}:{exp}".encode("utf-8")
    key = secret.encode("utf-8")
    return hmac.new(key, payload, hashlib.sha256).hexdigest()


def is_chunk_signature_valid(chunk_id: int, exp: int, sig: str, secret: str) -> bool:
    if exp < int(time.time()):
        return False

    expected = build_chunk_signature(chunk_id, exp, secret)
    return hmac.compare_digest(expected, sig)


def is_internal_token_valid(provided: str | None, expected: str) -> bool:
    if not provided:
        return False
    return hmac.compare_digest(provided, expected)
