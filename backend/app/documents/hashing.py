"""Cryptographic hashing for document content deduplication."""

import hashlib


def compute_sha256(data: bytes) -> str:
    """Compute hex SHA-256 checksum over byte payload."""
    hasher = hashlib.sha256()
    hasher.update(data)
    return hasher.hexdigest()
