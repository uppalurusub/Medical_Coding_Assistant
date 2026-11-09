import os
import sys

from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.config.settings import settings
logger = settings.get_logger()

from app.routers.coding_router import (
    router as coding_router
)


# =====================================================
# Configure Loguru
# =====================================================

LOG_DIR = settings.log_dir

logger.remove()

logger.add(
    sys.stdout,
    level="INFO",
    colorize=True,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
)

logger.add(
    f"{LOG_DIR}/medical_coding.log",
    rotation="10 MB",
    retention="30 days",
    compression="zip",
    level="INFO",
    enqueue=True
)


# =====================================================
# Application Lifecycle
# =====================================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info(
        "Starting Medical Coding Assistant API..."
    )

    logger.success(
        "Application Startup Completed"
    )

    yield

    logger.warning(
        "Shutting Down Medical Coding Assistant API..."
    )

    logger.success(
        "Application Shutdown Completed"
    )


# =====================================================
# FastAPI App
# =====================================================

app = FastAPI(
    title="Medical Coding Assistant API",
    description="""
Medical Coding Assistant using:

- LangChain
- Tool Calling
- Structured Output
- FastAPI
- Loguru

Features:
- ICD-10 Code Generation
- CPT Code Generation
- Coding Validation
- Confidence Scoring
""",
    version="1.0.0",
    lifespan=lifespan
)


# =====================================================
# Routers
# =====================================================

app.include_router(
    coding_router,
    prefix="/api/v1",
    tags=["Medical Coding"]
)


# =====================================================
# Root Endpoint
# =====================================================

@app.get("/")
async def root():

    logger.info(
        "Root Endpoint Invoked"
    )

    return {
        "application": "Medical Coding Assistant",
        "version": "1.0.0",
        "status": "RUNNING"
    }


# =====================================================
# Health Check
# =====================================================

@app.get("/health")
async def health_check():

    logger.info(
        "Health Check Endpoint Invoked"
    )

    return {
        "status": "UP",
        "service": "Medical Coding Assistant API"
    }


# =====================================================
# Startup Verification
# =====================================================

logger.success(
    "Main Application Loaded Successfully"
)