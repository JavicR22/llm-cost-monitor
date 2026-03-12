import pytest
from jose import JWTError

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)

USER_ID = "00000000-0000-0000-0000-000000000001"
ORG_ID = "00000000-0000-0000-0000-000000000002"


class TestPasswordHashing:
    def test_hash_is_not_plaintext(self) -> None:
        assert hash_password("secret123") != "secret123"

    def test_verify_correct_password(self) -> None:
        hashed = hash_password("correct-horse")
        assert verify_password("correct-horse", hashed) is True

    def test_verify_wrong_password(self) -> None:
        hashed = hash_password("correct-horse")
        assert verify_password("wrong-horse", hashed) is False

    def test_two_hashes_of_same_password_differ(self) -> None:
        # bcrypt uses a random salt each time
        assert hash_password("same") != hash_password("same")


class TestJWT:
    def test_access_token_decode(self) -> None:
        token = create_access_token(USER_ID, ORG_ID, "owner")
        payload = decode_token(token)
        assert payload["sub"] == USER_ID
        assert payload["org_id"] == ORG_ID
        assert payload["role"] == "owner"
        assert payload["type"] == "access"

    def test_refresh_token_decode(self) -> None:
        token = create_refresh_token(USER_ID)
        payload = decode_token(token)
        assert payload["sub"] == USER_ID
        assert payload["type"] == "refresh"

    def test_access_token_has_no_role_in_refresh(self) -> None:
        token = create_refresh_token(USER_ID)
        payload = decode_token(token)
        assert "role" not in payload

    def test_tampered_token_raises(self) -> None:
        token = create_access_token(USER_ID, ORG_ID, "owner")
        tampered = token[:-4] + "XXXX"
        with pytest.raises(JWTError):
            decode_token(tampered)

    def test_different_users_get_different_tokens(self) -> None:
        t1 = create_access_token(USER_ID, ORG_ID, "owner")
        t2 = create_access_token("other-id", ORG_ID, "viewer")
        assert t1 != t2
