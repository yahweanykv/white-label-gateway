"""Re-export shared SQLAlchemy models to keep backward compatibility."""

from shared.models.db import Merchant

__all__ = ["Merchant"]

