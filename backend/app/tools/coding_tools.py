from typing import Dict, List

from langchain_core.tools import tool
from app.config.settings import settings
logger = settings.get_logger()


# ---------------------------------------------------------
# Sample ICD-10 Repository
# Replace with Database / Vector Store / API
# ---------------------------------------------------------

ICD10_CODES = {
    "diabetes": {
        "code": "E11.9",
        "description": "Type 2 diabetes mellitus without complications"
    },
    "diabetic neuropathy": {
        "code": "E11.40",
        "description": "Type 2 diabetes mellitus with diabetic neuropathy"
    },
    "hypertension": {
        "code": "I10",
        "description": "Essential hypertension"
    },
    "asthma": {
        "code": "J45.909",
        "description": "Unspecified asthma, uncomplicated"
    }
}


# ---------------------------------------------------------
# Sample CPT Repository
# Replace with Database / Vector Store / API
# ---------------------------------------------------------

CPT_CODES = {
    "office visit": {
        "code": "99213",
        "description": "Established patient office visit"
    },
    "foot examination": {
        "code": "2028F",
        "description": "Foot examination performed"
    },
    "blood pressure check": {
        "code": "93784",
        "description": "Blood pressure monitoring"
    }
}


# ---------------------------------------------------------
# ICD Lookup Tool
# ---------------------------------------------------------

@tool
def icd_lookup_tool(diagnosis: str) -> Dict:
    """
    Lookup ICD-10 code from diagnosis text.
    """

    try:

        logger.info(
            f"Searching ICD-10 code for diagnosis: {diagnosis}"
        )

        diagnosis_lower = diagnosis.lower()

        for keyword, value in ICD10_CODES.items():

            if keyword in diagnosis_lower:

                logger.success(
                    f"ICD-10 code found: {value['code']}"
                )

                return {
                    "status": "SUCCESS",
                    "code": value["code"],
                    "description": value["description"]
                }

        logger.warning(
            f"No ICD-10 code found for diagnosis: {diagnosis}"
        )

        return {
            "status": "NOT_FOUND",
            "code": "",
            "description": "No matching ICD-10 code found"
        }

    except Exception as ex:

        logger.exception(
            f"ICD Lookup Error: {str(ex)}"
        )

        return {
            "status": "ERROR",
            "message": str(ex)
        }


# ---------------------------------------------------------
# CPT Lookup Tool
# ---------------------------------------------------------

@tool
def cpt_lookup_tool(procedure: str) -> Dict:
    """
    Lookup CPT code from procedure text.
    """

    try:

        logger.info(
            f"Searching CPT code for procedure: {procedure}"
        )

        procedure_lower = procedure.lower()

        for keyword, value in CPT_CODES.items():

            if keyword in procedure_lower:

                logger.success(
                    f"CPT code found: {value['code']}"
                )

                return {
                    "status": "SUCCESS",
                    "code": value["code"],
                    "description": value["description"]
                }

        logger.warning(
            f"No CPT code found for procedure: {procedure}"
        )

        return {
            "status": "NOT_FOUND",
            "code": "",
            "description": "No matching CPT code found"
        }

    except Exception as ex:

        logger.exception(
            f"CPT Lookup Error: {str(ex)}"
        )

        return {
            "status": "ERROR",
            "message": str(ex)
        }


# ---------------------------------------------------------
# Combined Coding Tool
# ---------------------------------------------------------

@tool
def medical_coding_tool(
    diagnosis: str,
    procedure: str
) -> Dict:
    """
    Generate ICD-10 and CPT coding suggestions.
    """

    try:

        logger.info(
            "Generating Medical Coding Suggestions"
        )

        icd_result = icd_lookup_tool.invoke(
            {"diagnosis": diagnosis}
        )

        cpt_result = cpt_lookup_tool.invoke(
            {"procedure": procedure}
        )

        response = {
            "diagnosis": diagnosis,
            "procedure": procedure,
            "icd10": icd_result,
            "cpt": cpt_result
        }

        logger.success(
            "Medical coding suggestions generated successfully"
        )

        return response

    except Exception as ex:

        logger.exception(
            f"Medical Coding Tool Error: {str(ex)}"
        )

        return {
            "status": "ERROR",
            "message": str(ex)
        }