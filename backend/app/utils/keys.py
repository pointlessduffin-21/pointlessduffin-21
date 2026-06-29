import secrets
import hashlib
from app.utils.auth import hash_password, verify_password


def generate_api_key() -> tuple[str, str, str]:
    """Returns (full_key, prefix, key_hash).  Prefix is first 8 chars for display."""
    raw = secrets.token_hex(24)  # 48-char hex key
    prefix = raw[:8]
    key_hash = hash_password(raw)
    return raw, prefix, key_hash


def generate_key_prefix_from_full(full_key: str) -> str:
    return full_key[:8]
