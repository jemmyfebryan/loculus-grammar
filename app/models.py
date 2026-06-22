"""Pydantic models for request and response validation."""
from typing import Annotated, Optional
from pydantic import BaseModel, Field


class Coordinate(BaseModel):
    """Coordinate in the grid."""
    x: int
    y: int


class GridAuthRequest(BaseModel):
    """Grid authentication request."""
    sequence: list[Coordinate] = Field(..., min_length=5, description="Ordered sequence of grid coordinates")


class ChangePasswordRequest(BaseModel):
    """Change password request."""
    action: str = Field(..., description="Action: 'verify_current' or 'change_password'")
    sequence: Optional[list[Coordinate]] = Field(None, description="Current password sequence for verification")
    new_sequence: Optional[list[Coordinate]] = Field(None, description="New password sequence")


class GrammarCheckRequest(BaseModel):
    text: Annotated[str, Field(min_length=1, description="Text to check grammar for")]
    context: Optional[str] = Field(None, description="Additional context to improve grammar correction")
    keep_writing_style: Optional[bool] = Field(False, description="Keep the original writing style")
    custom_instructions: Optional[str] = Field(None, description="Custom instructions for grammar correction")
    show_explanations: Optional[bool] = Field(False, description="Show explanations for corrections")
    multiple_outputs: Optional[int] = Field(1, ge=1, le=5, description="Number of alternative outputs (1-5)")


class GrammarOutput(BaseModel):
    text: str
    explanation: Optional[str] = None


class GrammarCheckResponse(BaseModel):
    original: str
    corrected: Optional[str] = None
    explanation: Optional[str] = None
    outputs: Optional[list[GrammarOutput]] = None
