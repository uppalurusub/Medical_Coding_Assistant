from fastapi import (
    APIRouter,
    HTTPException,
    status
)

from app.config.settings import settings
logger = settings.get_logger()

from app.services.coding_service import (
    MedicalCodingService
)

from app.schemas.request_model import (
    MedicalCodingRequest
)

from app.schemas.response_model import (
    MedicalCodingResponse
)

router = APIRouter()

coding_service = MedicalCodingService()


@router.post(
    "/medical-coding",
    response_model=MedicalCodingResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate ICD-10 and CPT Codes",
    description="""
Generate medical coding recommendations based on:

- Diagnosis
- Procedure
- Clinical Notes

Returns:

- ICD-10 Codes
- CPT Codes
- Coding Notes
- Confidence Score
- Validation Status
"""
)
async def generate_medical_codes(
    request: MedicalCodingRequest
) -> MedicalCodingResponse:

    try:

        logger.info(
            "Medical Coding API Request Received"
        )

        logger.info(
            f"""
            User ID    : {request.user_id}
            Session ID : {request.session_id}
            Language   : {request.language}
            """
        )

        response = coding_service.generate_codes(
            request
        )

        logger.success(
            "Medical Coding API Request Completed"
        )

        return response

    except ValueError as ve:

        logger.error(
            f"Validation Error: {str(ve)}"
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )

    except Exception as ex:

        logger.exception(
            f"Medical Coding API Error: {str(ex)}"
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate medical coding response."
        )