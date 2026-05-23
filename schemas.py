"""
Data models — request/response schemas using Pydantic
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from datetime import datetime
from enum import Enum
import uuid


# ── Enums ─────────────────────────────────────────────────────────────────────

class Severity(str, Enum):
    SEVERE   = "severe"
    MODERATE = "moderate"
    MILD     = "mild"


class OverallStatus(str, Enum):
    DANGER  = "danger"
    CAUTION = "caution"
    SAFE    = "safe"


# ── OCR models ─────────────────────────────────────────────────────────────────

class OCRRequest(BaseModel):
    """For base64 image uploads"""
    image_base64: str = Field(..., description="Base64-encoded image data")
    media_type: str   = Field(default="image/jpeg", description="MIME type of the image")


class OCRResponse(BaseModel):
    success: bool
    medications: list[str] = Field(default_factory=list, description="Extracted medication names")
    raw_text: Optional[str] = Field(None, description="All text extracted from the image")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    message: str = ""


# ── Interaction models ─────────────────────────────────────────────────────────

class InteractionCheckRequest(BaseModel):
    medications: list[str] = Field(..., min_length=2, description="List of medication names")
    patient_age: Optional[int] = Field(None, ge=0, le=130, description="Patient age for age-specific warnings")
    patient_conditions: Optional[list[str]] = Field(default_factory=list, description="Known conditions (e.g. kidney disease)")

    @field_validator("medications")
    @classmethod
    def validate_medications(cls, v):
        cleaned = [m.strip() for m in v if m.strip()]
        if len(cleaned) < 2:
            raise ValueError("At least 2 medications are required")
        if len(cleaned) > 20:
            raise ValueError("Maximum 20 medications per check")
        return cleaned


class DrugInteraction(BaseModel):
    drugs: list[str]       = Field(..., description="The two drugs involved")
    severity: Severity
    description: str       = Field(..., description="Clinical description of the interaction")
    action: str            = Field(..., description="Recommended action for the patient")
    mechanism: Optional[str] = Field(None, description="Pharmacological mechanism (if available)")


class InteractionCheckResponse(BaseModel):
    check_id: str               = Field(default_factory=lambda: str(uuid.uuid4()))
    medications: list[str]
    interactions: list[DrugInteraction]
    overall: OverallStatus
    summary: str
    severe_count: int           = 0
    moderate_count: int         = 0
    mild_count: int             = 0
    disclaimer: str             = (
        "This information is for educational purposes only. "
        "Always consult your doctor or pharmacist before making any medication decisions."
    )
    checked_at: datetime        = Field(default_factory=datetime.utcnow)

    def model_post_init(self, __context):
        self.severe_count   = sum(1 for i in self.interactions if i.severity == Severity.SEVERE)
        self.moderate_count = sum(1 for i in self.interactions if i.severity == Severity.MODERATE)
        self.mild_count     = sum(1 for i in self.interactions if i.severity == Severity.MILD)


# ── History models ─────────────────────────────────────────────────────────────

class HistoryEntry(BaseModel):
    id: str                         = Field(default_factory=lambda: str(uuid.uuid4()))
    medications: list[str]
    overall: OverallStatus
    severe_count: int
    checked_at: datetime


class HistoryResponse(BaseModel):
    entries: list[HistoryEntry]
    total: int


# ── Error model ────────────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    code: Optional[str]   = None
