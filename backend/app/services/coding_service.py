import json
import os
import time
from datetime import datetime

import mlflow
from langsmith import traceable

from app.config.settings import settings
logger = settings.get_logger()

from app.implementations.coding_impl import MedicalCodingImplementation
from app.schemas.request_model import MedicalCodingRequest
from app.schemas.response_model import MedicalCodingResponse

mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000"))
mlflow.set_experiment(os.getenv("MLFLOW_EXPERIMENT_NAME", "Medical_Coding_Assistant_Interface"))


class MedicalCodingService:
    def __init__(self):
        logger.info("Initializing Medical Coding Service")
        self.impl = MedicalCodingImplementation()
        logger.success("Medical Coding Service Initialized")

    @traceable(
        name="medical-coding-api-workflow",
        run_type="chain",
        tags=["healthcare", "medical-coding", "fastapi", "mlflow"],
        metadata={"endpoint": "/medical-coding", "feature": "medical_coding"},
    )
    def generate_codes(self, request: MedicalCodingRequest) -> MedicalCodingResponse:
        start = time.perf_counter()
        start_time = datetime.now()
        try:
            with mlflow.start_run(
                run_name=f"Medical_Coding_{start_time.strftime('%Y%m%d_%H%M%S')}",
                nested=mlflow.active_run() is not None,
            ):
                # Keep identifiers as tags; do not store full clinical notes in MLflow params.
                mlflow.log_param("start_time", start_time.isoformat(timespec="seconds"))
                mlflow.log_param("language", request.language)
                mlflow.log_param("model", os.getenv("fallback_model_1") or os.getenv("OPENROUTER_MODEL", "unknown"))
                mlflow.set_tag("source", "FastAPI")
                mlflow.set_tag("endpoint", "/medical-coding")
                mlflow.set_tag("session_id", request.session_id)
                mlflow.set_tag("user_id", request.user_id)
                mlflow.set_tag("langsmith_project", os.getenv("LANGSMITH_PROJECT", "medical-coding-assistant"))

                try:
                    response = self.impl.generate_codes(
                        diagnosis=request.diagnosis,
                        procedure=request.procedure,
                        clinical_notes=request.clinical_notes or "",
                        language=request.language,
                    )
                finally:
                    # Log usage even when the provider returned usage but structured parsing failed.
                    telemetry = getattr(self.impl, "last_telemetry", {})
                    elapsed = round(time.perf_counter() - start, 4)
                    for metric in ("input_tokens", "output_tokens", "total_tokens", "execution_time_seconds"):
                        value = telemetry.get(metric)
                        if value is not None:
                            mlflow.log_metric(metric, float(value))
                    for metric in ("input_cost_usd", "output_cost_usd", "total_cost_usd"):
                        value = telemetry.get(metric)
                        if value is not None:
                            mlflow.log_metric(metric, float(value))
                    mlflow.set_tag("usage_source", telemetry.get("usage_source", "unavailable"))
                    if telemetry.get("model_name"):
                        mlflow.set_tag("actual_model", str(telemetry["model_name"]))
                    mlflow.set_tag("llm_status", "success" if "response" in locals() else "failed")
                    mlflow.log_metric("service_execution_time_seconds", elapsed)
                    mlflow.log_param("input",request)
                    mlflow.log_param("output",response)
                    logger.info(f"MLflow logged LLM telemetry (including failed calls): {telemetry}")
                return response
        except Exception as ex:
            logger.exception(f"Medical Coding Service Error: {str(ex)}")
            raise Exception(f"Medical Coding Service Failed: {str(ex)}") from ex
