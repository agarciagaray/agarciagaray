"""Primitivas criptográficas de la bóveda bancaria.

La contraseña de acceso nunca se almacena. Se usa Argon2id para derivar una
clave de 256 bits y AES-GCM para cifrar cada valor sensible con nonce único.
"""
from __future__ import annotations

import base64
import os
from dataclasses import dataclass

from argon2.low_level import Type, hash_secret_raw
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

MAGIC = b"BV1"

@dataclass(frozen=True)
class KeyMaterial:
    key: bytes
    salt: bytes


def derive_key(password: str, salt: bytes) -> bytes:
    if not password or len(password) < 10:
        raise ValueError("La contraseña debe tener al menos 10 caracteres")
    return hash_secret_raw(
        password.encode("utf-8"), salt, time_cost=3, memory_cost=65536,
        parallelism=2, hash_len=32, type=Type.ID,
    )


def new_key_material(password: str) -> KeyMaterial:
    salt = os.urandom(16)
    return KeyMaterial(derive_key(password, salt), salt)


def encrypt(value: str | None, key: bytes) -> str | None:
    if value is None or value == "":
        return None
    nonce = os.urandom(12)
    ciphertext = AESGCM(key).encrypt(nonce, value.encode("utf-8"), MAGIC)
    return base64.urlsafe_b64encode(MAGIC + nonce + ciphertext).decode("ascii")


def decrypt(token: str | None, key: bytes) -> str | None:
    if not token:
        return None
    raw = base64.urlsafe_b64decode(token.encode("ascii"))
    if raw[:3] != MAGIC:
        raise ValueError("Formato de dato cifrado no reconocido")
    return AESGCM(key).decrypt(raw[3:15], raw[15:], MAGIC).decode("utf-8")


def mask(value: str | None, visible: int = 4) -> str:
    if not value:
        return "—"
    if len(value) <= visible:
        return "•" * len(value)
    return "•" * max(4, len(value) - visible) + value[-visible:]
