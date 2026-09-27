"""Zero-Retention Privacy Vault & LGPD Tokenizer for Sensitive Executive Remuneration.

Implements bi-directional surrogate tokenization with cryptographic shredding (LGPD Art. 18),
preventing executive PII and individual compensation figures from leaking into LLM inference contexts.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import re
from dataclasses import dataclass


@dataclass
class TokenVaultRecord:
    surrogate_token: str
    original_value: str
    category: str


class ExecutivePrivacyVault:
    """In-memory zero-retention vault for pseudonymizing executive identifiers and compensation figures."""

    def __init__(self, secret_key: bytes | None = None) -> None:
        self._secret_key = secret_key or os.urandom(32)
        self._forward_map: dict[str, TokenVaultRecord] = {}
        self._reverse_map: dict[str, str] = {}
        self._is_shredded: bool = False

    def tokenize_identifier(self, raw_id: str, category: str = "EXECUTIVE_ID") -> str:
        """Deterministically generates an opaque surrogate token from a raw identifier (e.g. CPF, Name)."""
        if self._is_shredded:
            raise RuntimeError("Privacy vault has been cryptographically shredded.")

        clean_id = raw_id.strip()
        if clean_id in self._forward_map:
            return self._forward_map[clean_id].surrogate_token

        digest = hmac.new(self._secret_key, clean_id.encode("utf-8"), hashlib.sha256).hexdigest()[:12]
        token = f"[SEC_{category}_{digest.upper()}]"

        record = TokenVaultRecord(surrogate_token=token, original_value=clean_id, category=category)
        self._forward_map[clean_id] = record
        self._reverse_map[token] = clean_id
        return token

    def detokenize(self, text_with_tokens: str) -> str:
        """Substitutes surrogate tokens back with original values upon authorized egress."""
        if self._is_shredded:
            raise RuntimeError("Privacy vault has been cryptographically shredded.")

        result = text_with_tokens
        token_pattern = re.compile(r"\[SEC_[A-Z_]+_[A-F0-9]{12}\]")

        for token in token_pattern.findall(text_with_tokens):
            if token in self._reverse_map:
                result = result.replace(token, self._reverse_map[token])

        return result

    def shred(self) -> None:
        """Cryptographically shreds all in-memory keys and mapping tables (LGPD Art. 18)."""
        self._forward_map.clear()
        self._reverse_map.clear()
        self._secret_key = b"\x00" * 32
        self._is_shredded = True
