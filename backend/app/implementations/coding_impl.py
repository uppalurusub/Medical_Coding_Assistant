import os
import time
from typing import Optional, Any, Dict

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.prompts import ChatPromptTemplate
from langsmith import traceable



from app.config.settings import settings
logger = settings.get_logger()

from app.prompts.coding_prompt import CodingPrompt
from app.schemas.response_model import MedicalCodingResponse


def _to_number(value):
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


class UsageCaptureHandler(BaseCallbackHandler):
    """Capture token/cost metadata from the actual LLM response, not the Pydantic API model."""

    def __init__(self):
        self.input_tokens = 0
        self.output_tokens = 0
        self.total_tokens = 0
        self.input_cost_usd = None
        self.output_cost_usd = None
        self.total_cost_usd = None
        self.source = "unavailable"
        self.model_name = None
        self.raw_usage = {}

    def on_llm_end(self, response, **kwargs):
        try:
            generation = response.generations[0][0]
            message = getattr(generation, "message", None)
            usage = getattr(message, "usage_metadata", None) or {}
            metadata = getattr(message, "response_metadata", None) or {}
            token_usage = metadata.get("token_usage") or metadata.get("usage") or {}
            # OpenAI-compatible usage can be found in either location.
            input_tokens = usage.get("input_tokens", token_usage.get("prompt_tokens", token_usage.get("input_tokens", 0)))
            output_tokens = usage.get("output_tokens", token_usage.get("completion_tokens", token_usage.get("output_tokens", 0)))
            total_tokens = usage.get("total_tokens", token_usage.get("total_tokens", 0))
            self.input_tokens += int(input_tokens or 0)
            self.output_tokens += int(output_tokens or 0)
            self.total_tokens += int(total_tokens or (int(input_tokens or 0) + int(output_tokens or 0)))

            self.model_name = metadata.get("model_name") or metadata.get("model") or self.model_name
            # OpenRouter may include provider-reported cost in response metadata/usage.
            cost = metadata.get("cost")
            if cost is None:
                cost = token_usage.get("cost")
            if cost is None:
                cost = (metadata.get("usage") or {}).get("cost") if isinstance(metadata.get("usage"), dict) else None
            cost = _to_number(cost)
            if cost is not None:
                self.total_cost_usd = (self.total_cost_usd or 0.0) + cost
                self.source = "provider_reported"

            # If provider cost is absent, use explicitly configured per-million token rates.
            # Do not claim these are provider-reported costs.
            input_rate = _to_number(os.getenv("LLM_INPUT_COST_PER_1M_TOKENS"))
            output_rate = _to_number(os.getenv("LLM_OUTPUT_COST_PER_1M_TOKENS"))
            if self.source != "provider_reported" and input_rate is not None and output_rate is not None:
                self.input_cost_usd = self.input_tokens * input_rate / 1_000_000
                self.output_cost_usd = self.output_tokens * output_rate / 1_000_000
                self.total_cost_usd = self.input_cost_usd + self.output_cost_usd
                self.source = "configured_rate_estimate"

            self.raw_usage = {
                "usage_metadata": usage,
                "response_metadata": metadata,
            }
        except Exception as exc:
            logger.warning(f"Could not extract LLM usage metadata: {exc}")


    def on_llm_error(self, error, **kwargs):
        """Capture usage attached to provider exceptions (e.g. finish_reason=length)."""
        try:
            completion = getattr(error, "completion", None)
            usage_obj = getattr(completion, "usage", None) if completion is not None else None
            if usage_obj is None and completion is not None:
                usage_obj = getattr(completion, "usage_metadata", None)
            if usage_obj is None:
                return

            if hasattr(usage_obj, "model_dump"):
                usage = usage_obj.model_dump()
            elif isinstance(usage_obj, dict):
                usage = usage_obj
            else:
                usage = {
                    "prompt_tokens": getattr(usage_obj, "prompt_tokens", 0),
                    "completion_tokens": getattr(usage_obj, "completion_tokens", 0),
                    "total_tokens": getattr(usage_obj, "total_tokens", 0),
                    "cost": getattr(usage_obj, "cost", None),
                    "cost_details": getattr(usage_obj, "cost_details", None),
                }

            self.input_tokens = max(self.input_tokens, int(usage.get("prompt_tokens", usage.get("input_tokens", 0)) or 0))
            self.output_tokens = max(self.output_tokens, int(usage.get("completion_tokens", usage.get("output_tokens", 0)) or 0))
            self.total_tokens = max(self.total_tokens, int(usage.get("total_tokens", 0) or (self.input_tokens + self.output_tokens)))

            cost = _to_number(usage.get("cost"))
            cost_details = usage.get("cost_details") or {}
            if cost is not None:
                self.total_cost_usd = cost
                self.input_cost_usd = _to_number(cost_details.get("upstream_inference_prompt_cost"))
                self.output_cost_usd = _to_number(cost_details.get("upstream_inference_completions_cost"))
                self.source = "provider_reported"
            self.raw_usage = {"exception_usage": usage, "error_type": type(error).__name__}
            logger.warning(
                f"Captured usage from failed LLM response: input_tokens={self.input_tokens}, "
                f"output_tokens={self.output_tokens}, total_tokens={self.total_tokens}, "
                f"cost_usd={self.total_cost_usd}, source={self.source}"
            )
        except Exception as exc:
            logger.warning(f"Could not extract usage from LLM error: {exc}")

    def as_dict(self):
        return {
            "input_tokens": int(self.input_tokens),
            "output_tokens": int(self.output_tokens),
            "total_tokens": int(self.total_tokens),
            "input_cost_usd": self.input_cost_usd,
            "output_cost_usd": self.output_cost_usd,
            "total_cost_usd": self.total_cost_usd,
            "usage_source": self.source,
            "model_name": self.model_name,
        }


class MedicalCodingImplementation:
    def __init__(self):
        logger.info("Initializing Medical Coding Implementation")
        self.llm = settings.get_model_client()
        self.structured_llm = self.llm.with_structured_output(
            MedicalCodingResponse,
            method="function_calling",
            strict=False,
        )
        logger.success("Medical Coding Implementation Initialized")

    @traceable(
        name="medical-coding-generate",
        run_type="chain",
        tags=["healthcare", "medical-coding", "openrouter", "structured-output"],
        metadata={"feature": "medical_coding", "component": "MedicalCodingImplementation"},
    )
    def generate_codes(
        self,
        diagnosis: str,
        procedure: str,
        clinical_notes: Optional[str] = "",
        language: str = "English",
    ) -> MedicalCodingResponse:
        started = time.perf_counter()
        usage_handler = UsageCaptureHandler()
        try:
            logger.info("Starting Medical Coding Generation")
            prompt = ChatPromptTemplate.from_messages([
                ("system", CodingPrompt.get_system_prompt()),
                ("human", CodingPrompt.build_prompt(
                    diagnosis=diagnosis,
                    procedure=procedure,
                    clinical_notes=clinical_notes or "",
                    language=language,
                )),
            ])
            chain = prompt | self.structured_llm
            response = chain.invoke(
                {},
                config={
                    "callbacks": [usage_handler],
                    "run_name": "medical_coding_structured_llm",
                    "tags": ["healthcare", "medical-coding", "openrouter"],
                    "metadata": {
                        "feature": "medical_coding",
                        "language": language,
                        "model": os.getenv("fallback_model_1") or os.getenv("OPENROUTER_MODEL", "unknown"),
                    },
                },
            )
            elapsed = round(time.perf_counter() - started, 4)
            usage = usage_handler.as_dict()
            logger.info(f"LLM usage and cost: {usage}; execution_time_seconds={elapsed}")
            # Attach telemetry for service/MLflow logging while preserving the response schema.
            self.last_telemetry = {**usage, "execution_time_seconds": elapsed}
            logger.success("Medical Coding Generated Successfully")
            return response
        except Exception as ex:
            elapsed = round(time.perf_counter() - started, 4)
            usage = usage_handler.as_dict()
            self.last_telemetry = {**usage, "execution_time_seconds": elapsed}
            logger.error(f"LLM invocation failed; captured telemetry={self.last_telemetry}")
            logger.exception(f"Medical Coding Error: {str(ex)}")
            raise Exception(f"Medical Coding Generation Failed: {str(ex)}") from ex
