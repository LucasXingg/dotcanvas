"""File-backed API token store for DotCanvas."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List
import hashlib
import json
import secrets


@dataclass
class TokenRecord:
    token_id: str
    name: str
    preview: str
    created_at: str
    token_hash: str

    @classmethod
    def from_dict(cls, data: dict) -> "TokenRecord":
        return cls(
            token_id=str(data.get("id", "")),
            name=str(data.get("name", "")),
            preview=str(data.get("preview", "")),
            created_at=str(data.get("created_at", "")),
            token_hash=str(data.get("token_hash", "")),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.token_id,
            "name": self.name,
            "preview": self.preview,
            "created_at": self.created_at,
            "token_hash": self.token_hash,
        }


class TokenStoreError(RuntimeError):
    """Raised when token store operations fail."""


class TokenStore:
    """Simple JSON-backed token storage with constant-time verification."""

    DEFAULT_PATH = Path(__file__).resolve().parents[1] / "configs" / "tokens.json"

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path else self.DEFAULT_PATH
        self._tokens: List[TokenRecord] = []
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            self._tokens = []
            return
        try:
            with self.path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except json.JSONDecodeError as exc:  # pragma: no cover - configuration error
            raise TokenStoreError(f"Invalid token store JSON: {exc.msg}") from exc
        if not isinstance(payload, list):
            raise TokenStoreError("Token store must contain a JSON array")
        self._tokens = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            record = TokenRecord.from_dict(item)
            if record.token_id and record.token_hash:
                self._tokens.append(record)

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as handle:
            json.dump([record.to_dict() for record in self._tokens], handle, ensure_ascii=False, indent=2)

    def list_tokens(self) -> List[dict]:
        return [
            {
                "id": record.token_id,
                "name": record.name,
                "preview": record.preview,
                "created_at": record.created_at,
            }
            for record in self._tokens
        ]

    def _hash(self, token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def _generate_token(self) -> str:
        return secrets.token_urlsafe(32)

    def create_token(self, *, name: str = "") -> tuple[str, dict]:
        raw_token = self._generate_token()
        token_id = secrets.token_hex(8)
        preview = f"{raw_token[:4]}…{raw_token[-4:]}"
        created_at = datetime.utcnow().isoformat() + "Z"
        record = TokenRecord(
            token_id=token_id,
            name=name,
            preview=preview,
            created_at=created_at,
            token_hash=self._hash(raw_token),
        )
        self._tokens.append(record)
        self._save()
        return raw_token, {
            "id": token_id,
            "name": name,
            "preview": preview,
            "created_at": created_at,
        }

    def delete_token(self, token_id: str) -> bool:
        original = len(self._tokens)
        self._tokens = [record for record in self._tokens if record.token_id != token_id]
        if len(self._tokens) != original:
            self._save()
            return True
        return False

    def verify(self, token: str) -> bool:
        if not token:
            return False
        candidate = self._hash(token)
        return any(secrets.compare_digest(candidate, record.token_hash) for record in self._tokens)

    def import_tokens(self, records: Iterable[dict]) -> None:
        self._tokens = []
        for item in records:
            if not isinstance(item, dict):
                continue
            record = TokenRecord.from_dict(item)
            if record.token_id and record.token_hash:
                self._tokens.append(record)
        self._save()


__all__ = ["TokenStore", "TokenStoreError"]
