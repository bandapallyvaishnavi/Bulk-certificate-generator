
from typing import Any

from pydantic import BaseModel, Field


class RecipientInput(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=254)
    course: str = Field(min_length=1, max_length=100)


class BulkCertificateRequest(BaseModel):
    recipients: list[dict[str, Any]] = Field(
        min_length=1,
        max_length=500
    )
