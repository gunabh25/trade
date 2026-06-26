from tradeflow.core.security.password import (
    generate_token,
    hash_password,
    hash_token,
    verify_password,
)


def test_hash_and_verify_password() -> None:
    hashed = hash_password("SecurePass1")
    assert verify_password("SecurePass1", hashed)
    assert not verify_password("WrongPass1", hashed)


def test_token_hash_is_deterministic() -> None:
    token = generate_token()
    assert hash_token(token) == hash_token(token)
    assert hash_token(token) != hash_token(generate_token())
