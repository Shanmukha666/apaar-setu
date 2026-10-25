"""Pure deterministic Ed25519 signed-record helpers. Owner: P6."""
import base64
import hashlib
import json
from functools import lru_cache

import qrcode
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64decode(value: str) -> bytes:
    if not value or any(char not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_" for char in value):
        raise ValueError("invalid base64url")
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


@lru_cache(maxsize=None)
def get_keypair(seed: str):
    private = Ed25519PrivateKey.from_private_bytes(hashlib.sha256(seed.encode("utf-8")).digest())
    return private, private.public_key()


def get_public_key_pem(seed: str) -> str:
    return get_keypair(seed)[1].public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode("ascii")


def canonical_json(payload: dict) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def build_payload(student: dict, institution_code: str, programme_code: str, issued_at: str) -> dict:
    return {"v": 1, "apaar_id": student["apaar_id"], "student_ref": student["student_ref"], "institution_code": institution_code, "programme_code": programme_code, "academic_year": student["academic_year"], "status": student["status"], "issued_at": issued_at}


def sign_payload(payload: dict, seed: str) -> str:
    encoded = canonical_json(payload)
    signature = get_keypair(seed)[0].sign(encoded)
    return f"{_b64encode(encoded)}.{_b64encode(signature)}"


def verify_token(token: str, seed: str) -> tuple[bool, dict | None, str]:
    try:
        payload_part, signature_part = token.split(".")
        encoded, signature = _b64decode(payload_part), _b64decode(signature_part)
    except (ValueError, UnicodeDecodeError):
        return False, None, "MALFORMED"
    try:
        get_keypair(seed)[1].verify(signature, encoded)
    except InvalidSignature:
        return False, None, "BAD_SIGNATURE"
    try:
        payload = json.loads(encoded.decode("utf-8"))
        if not isinstance(payload, dict):
            return False, None, "MALFORMED"
    except (UnicodeDecodeError, json.JSONDecodeError):
        return False, None, "MALFORMED"
    return True, payload, "OK"


def make_verify_url(token: str, frontend_url: str) -> str:
    return f"{frontend_url}/verify?t={token}"


def make_qr_png(data: str) -> bytes:
    image = qrcode.make(data)
    from io import BytesIO
    output = BytesIO(); image.save(output, format="PNG")
    return output.getvalue()
