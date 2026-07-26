from pydantic import BaseModel, Field


class FieldUpdate(BaseModel):
    field_name: str = Field(description="Patient record field name.")
    field_value: str = Field(description="Value to write into the field.")


class ReviewResult(BaseModel):
    approved: bool
    missing_fields: list[str] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)
