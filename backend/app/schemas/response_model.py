from pydantic import BaseModel, Field
from typing import List, Optional


class ICD10Code(BaseModel):
    code: str = Field(
        ...,
        description="ICD-10 diagnosis code"
    )

    description: str = Field(
        ...,
        description="ICD-10 code description"
    )

    confidence: float = Field(
        ...,
        description="Confidence score for ICD code"
    )


class CPTCode(BaseModel):
    code: str = Field(
        ...,
        description="CPT procedure code"
    )

    description: str = Field(
        ...,
        description="CPT code description"
    )

    confidence: float = Field(
        ...,
        description="Confidence score for CPT code"
    )


class CodingValidation(BaseModel):
    status: str = Field(
        ...,
        description="VALID / REVIEW_REQUIRED"
    )

    message: str = Field(
        ...,
        description="Validation remarks"
    )


class MedicalCodingResponse(BaseModel):
    diagnosis: str

    procedure: str

    icd10_codes: List[ICD10Code]

    cpt_codes: List[CPTCode]

    coding_notes: str

    confidence_score: float

    validation: CodingValidation

    language: str

    generated_by: str = "Medical Coding Assistant"

    class Config:
        json_schema_extra = {
            "example": {
                "diagnosis": "Type 2 diabetes mellitus with diabetic neuropathy",
                "procedure": "Comprehensive diabetic foot examination",
                "icd10_codes": [
                    {
                        "code": "E11.40",
                        "description": "Type 2 diabetes mellitus with diabetic neuropathy",
                        "confidence": 0.96
                    }
                ],
                "cpt_codes": [
                    {
                        "code": "99213",
                        "description": "Established patient office visit",
                        "confidence": 0.93
                    }
                ],
                "coding_notes": "Diagnosis and procedure support the assigned ICD-10 and CPT codes.",
                "confidence_score": 0.95,
                "validation": {
                    "status": "VALID",
                    "message": "Codes successfully validated."
                },
                "language": "English",
                "generated_by": "Medical Coding Assistant"
            }
        }