from app.services.signing import build_payload, canonical_json, make_qr_png, make_verify_url, sign_payload, verify_token

SEED = "apaar-setu-demo"
PAYLOAD = build_payload({"apaar_id":"100000000009","student_ref":"SYN-1","academic_year":"2026-27","status":"ACCEPTED"}, "DIT001", "DIT001-CSE", "2026-10-01T00:00:00Z")

def test_round_trip_and_determinism():
    token = sign_payload(PAYLOAD, SEED)
    assert verify_token(token, SEED) == (True, PAYLOAD, "OK")
    assert sign_payload(PAYLOAD, SEED) == token

def test_tampering_and_malformed_tokens():
    token = sign_payload(PAYLOAD, SEED); payload, signature = token.split(".")
    changed_payload = ("A" if payload[0] != "A" else "B") + payload[1:]
    changed_signature = ("A" if signature[0] != "A" else "B") + signature[1:]
    assert verify_token(f"{changed_payload}.{signature}", SEED)[2] == "BAD_SIGNATURE"
    assert verify_token(f"{payload}.{changed_signature}", SEED)[2] == "BAD_SIGNATURE"
    assert verify_token("no-dot", SEED)[2] == "MALFORMED"
    assert verify_token("@@.@@", SEED)[2] == "MALFORMED"

def test_wrong_seed_and_canonical_json():
    assert verify_token(sign_payload(PAYLOAD, SEED), "different")[2] == "BAD_SIGNATURE"
    assert canonical_json({"b": 2, "a": 1}) == canonical_json({"a": 1, "b": 2})

def test_qr_and_verify_url():
    assert make_qr_png("data").startswith(b"\x89PNG\r\n\x1a\n")
    assert make_verify_url("token", "http://localhost:3000") == "http://localhost:3000/verify?t=token"
