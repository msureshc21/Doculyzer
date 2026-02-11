"""API v1 package initialization."""
from app.api.v1 import health, documents, facts, autofill

__all__ = ["health", "documents", "facts", "autofill"]
