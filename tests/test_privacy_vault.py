"""Tests for zero-retention executive privacy vault & LGPD pseudonymization."""

from __future__ import annotations

import pytest

from relata.security.privacy_vault import ExecutivePrivacyVault


def test_vault_tokenization_and_detokenization() -> None:
    vault = ExecutivePrivacyVault()

    raw_cpf = "123.456.789-00"
    raw_name = "Carlos Eduardo da Silva"

    token_cpf = vault.tokenize_identifier(raw_cpf, category="CPF")
    token_name = vault.tokenize_identifier(raw_name, category="NAME")

    # Tokens must be opaque strings
    assert raw_cpf not in token_cpf
    assert raw_name not in token_name
    assert token_cpf.startswith("[SEC_CPF_")
    assert token_name.startswith("[SEC_NAME_")

    # Deterministic: same raw input yields same token
    assert vault.tokenize_identifier(raw_cpf, category="CPF") == token_cpf

    # Detokenization recovers original text
    text_prompt = f"O executivo {token_name} com documento {token_cpf} recebeu bônus de R$ 500.000,00."
    detokenized = vault.detokenize(text_prompt)

    assert raw_name in detokenized
    assert raw_cpf in detokenized
    assert "[SEC_" not in detokenized


def test_vault_cryptographic_shredding() -> None:
    vault = ExecutivePrivacyVault()
    token = vault.tokenize_identifier("Secret Executive", category="NAME")

    vault.shred()

    # Attempting any operation post-shredding must raise RuntimeError
    with pytest.raises(RuntimeError, match="cryptographically shredded"):
        vault.tokenize_identifier("Another Executive")

    with pytest.raises(RuntimeError, match="cryptographically shredded"):
        vault.detokenize(f"Hello {token}")
