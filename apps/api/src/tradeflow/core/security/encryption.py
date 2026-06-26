from __future__ import annotations

import base64
import hashlib
import json
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

from tradeflow.core.config import Settings


class EncryptionService:
    """Symmetric encryption for TOTP secrets and OAuth tokens at rest."""

    def __init__(self, settings: Settings) -> None:
        key_material = hashlib.sha256(settings.api_secret_key.encode()).digest()
        fernet_key = base64.urlsafe_b64encode(key_material)
        self._fernet = Fernet(fernet_key)

    def encrypt(self, value: str) -> str:
        return self._fernet.encrypt(value.encode("utf-8")).decode("utf-8")

    def decrypt(self, value: str) -> str:
        try:
            return self._fernet.decrypt(value.encode("utf-8")).decode("utf-8")
        except InvalidToken as exc:
            msg = "Failed to decrypt value"
            raise ValueError(msg) from exc

    def encrypt_json(self, data: Any) -> str:
        return self.encrypt(json.dumps(data))

    def decrypt_json(self, value: str) -> Any:
        return json.loads(self.decrypt(value))
