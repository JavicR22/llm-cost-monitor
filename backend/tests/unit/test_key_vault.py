import hashlib

import pytest
from cryptography.fernet import Fernet

from app.services.security.key_vault import KeyVault, KeyVaultError


@pytest.fixture
def vault() -> KeyVault:
    key = Fernet.generate_key().decode()
    return KeyVault(key)


class TestEncryption:
    def test_encrypt_decrypt_roundtrip(self, vault: KeyVault) -> None:
        plaintext = "sk-openai-super-secret-key-123"
        ciphertext = vault.encrypt(plaintext)
        assert vault.decrypt(ciphertext) == plaintext

    def test_ciphertext_differs_from_plaintext(self, vault: KeyVault) -> None:
        plaintext = "sk-openai-super-secret-key-123"
        assert vault.encrypt(plaintext) != plaintext

    def test_wrong_key_raises_error(self) -> None:
        vault_a = KeyVault(Fernet.generate_key().decode())
        vault_b = KeyVault(Fernet.generate_key().decode())
        ciphertext = vault_a.encrypt("secret")
        with pytest.raises(KeyVaultError):
            vault_b.decrypt(ciphertext)

    def test_tampered_ciphertext_raises_error(self, vault: KeyVault) -> None:
        ciphertext = vault.encrypt("secret")
        tampered = ciphertext[:-4] + "XXXX"
        with pytest.raises(KeyVaultError):
            vault.decrypt(tampered)

    def test_invalid_master_key_raises_error(self) -> None:
        with pytest.raises(KeyVaultError):
            KeyVault("not-a-valid-fernet-key")


class TestServiceKeyGeneration:
    def test_generate_returns_three_parts(self) -> None:
        raw_key, key_hash, key_prefix = KeyVault.generate_service_key()
        assert raw_key
        assert key_hash
        assert key_prefix

    def test_raw_key_has_correct_prefix(self) -> None:
        raw_key, _, _ = KeyVault.generate_service_key()
        assert raw_key.startswith("lcm_sk_live_")

    def test_hash_is_sha256_hex(self) -> None:
        raw_key, key_hash, _ = KeyVault.generate_service_key()
        assert key_hash == hashlib.sha256(raw_key.encode()).hexdigest()
        assert len(key_hash) == 64

    def test_hash_service_key_matches_stored_hash(self) -> None:
        raw_key, stored_hash, _ = KeyVault.generate_service_key()
        assert KeyVault.hash_service_key(raw_key) == stored_hash

    def test_two_keys_are_unique(self) -> None:
        key_a, _, _ = KeyVault.generate_service_key()
        key_b, _, _ = KeyVault.generate_service_key()
        assert key_a != key_b

    def test_prefix_does_not_expose_full_key(self) -> None:
        raw_key, _, key_prefix = KeyVault.generate_service_key()
        assert key_prefix != raw_key
        assert "***" in key_prefix
        assert len(key_prefix) < len(raw_key)
