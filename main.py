"""
MedScan Backend — Drug Interaction Warning System
FastAPI + Claude Vision OCR + Anthropic Drug Analysis
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
import logging

from routes.ocr import router as ocr_router
from routes.interactions import router as interactions_router
from routes.history import router as history_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("MedScan API starting up...")
    yield
    logger.info("MedScan API shutting down.")


app = FastAPI(
    title="MedScan API",
    description="OCR-powered drug interaction warning system for elderly patients",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Restrict to your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ocr_router,          prefix="/api/v1/ocr",          tags=["OCR"])
app.include_router(interactions_router, prefix="/api/v1/interactions",  tags=["Interactions"])
app.include_router(history_router,      prefix="/api/v1/history",       tags=["History"])


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "service": "MedScan API", "version": "1.0.0"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
