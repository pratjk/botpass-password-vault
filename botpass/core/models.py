import dataclasses
from datetime import datetime
from typing import Optional

@dataclasses.dataclass
class Entry:
    """Represents a single password entry."""
    id: Optional[int]
    domain_hmac: str
    username_enc: bytes
    password_enc: bytes
    nonce: bytes
    created_at: str
    updated_at: str
    
    # Keeping it simple, a beginner might use a dict for fast conversions
    def to_dict(self):
        return {
            "id": self.id,
            "domain_hmac": self.domain_hmac,
            "username_enc": self.username_enc,
            "password_enc": self.password_enc,
            "nonce": self.nonce,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
