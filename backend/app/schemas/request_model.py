from pydantic import BaseModel, Field
from typing import Optional


class MedicalCodingRequest(BaseModel):
    """
    Request model for Medical Coding Assistant
    """

    diagnosis: str = Field(
        ...,
        description="Patient diagnosis or clinical condition",
        examples=[
            "Type 2 diabetes mellitus with diabetic neuropathy"
        ]
    )

    procedure: str = Field(
        ...,
        description="Medical procedure performed",
        examples=[
            "Comprehensive diabetic foot examination"
        ]
    )

    clinical_notes: Optional[str] = Field(
        default=None,
        description="Additional clinical notes for coding assistance",
        examples=[
            "Patient has uncontrolled diabetes with neuropathic symptoms."
        ]
    )

    language: str = Field(
        default="English",
        description="Response language"
    )

    user_id: str = Field(
        ...,
        description="Unique user identifier",
        examples=["USR001"]
    )

    session_id: str = Field(
        ...,
        description="Unique session identifier",
        examples=["SES001"]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "diagnosis": "Type 2 diabetes mellitus with diabetic neuropathy",
                "procedure": "Comprehensive diabetic foot examination",
                "clinical_notes": "Patient complains of numbness and tingling in both feet.",
                "language": "English",
                "user_id": "USR001",
                "session_id": "SES001"
            }
        }