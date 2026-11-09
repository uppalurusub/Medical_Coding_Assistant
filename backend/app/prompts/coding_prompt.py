from app.config.settings import settings
logger = settings.get_logger()


logger.info(
    "Loading Medical Coding Prompt Templates..."
)


class CodingPrompt:

    SYSTEM_PROMPT = """
You are an expert Certified Medical Coding Specialist (CMS).

Your responsibilities:

1. Analyze diagnosis information.
2. Analyze procedure information.
3. Generate appropriate ICD-10 codes.
4. Generate appropriate CPT codes.
5. Provide coding notes.
6. Provide confidence scores.
7. Validate coding accuracy.

Rules:

- Return only valid JSON.
- Do not provide explanations outside JSON.
- Use standard ICD-10 coding guidelines.
- Use standard CPT coding guidelines.
- If insufficient information exists, mark validation status as REVIEW_REQUIRED.
- Confidence score must be between 0 and 1.
- Keep the response concise and schema-focused; do not repeat the clinical notes.
- Return only the best-supported codes (maximum 3 ICD-10 and 3 CPT candidates).
- Keep coding_notes to at most 2 short sentences.
- Do not include chain-of-thought, lengthy explanations, or markdown.
"""

    USER_PROMPT = """
Diagnosis:
{diagnosis}

Procedure:
{procedure}

Clinical Notes:
{clinical_notes}

Language:
{language}

Generate:

1. ICD-10 Codes
2. CPT Codes
3. Coding Notes
4. Confidence Score
5. Validation Status

Return a compact response matching the schema exactly. Populate every required field.
For each code, provide only the code, a short description, and a confidence value.
If the documentation does not support a code, do not guess; set validation to REVIEW_REQUIRED.
"""

    @classmethod
    def get_system_prompt(cls) -> str:
        """
        Returns system prompt.
        """

        logger.info(
            "Fetching Medical Coding System Prompt"
        )

        return cls.SYSTEM_PROMPT

    @classmethod
    def get_user_prompt(cls) -> str:
        """
        Returns user prompt.
        """

        logger.info(
            "Fetching Medical Coding User Prompt"
        )

        return cls.USER_PROMPT

    @classmethod
    def build_prompt(
        cls,
        diagnosis: str,
        procedure: str,
        clinical_notes: str,
        language: str
    ) -> str:
        """
        Build final prompt.
        """

        logger.info(
            "Building Medical Coding Prompt"
        )

        prompt = cls.USER_PROMPT.format(
            diagnosis=diagnosis,
            procedure=procedure,
            clinical_notes=clinical_notes,
            language=language
        )

        logger.debug(
            f"Generated Prompt:\n{prompt}"
        )

        return prompt


logger.success(
    "Medical Coding Prompt Templates Loaded Successfully"
)