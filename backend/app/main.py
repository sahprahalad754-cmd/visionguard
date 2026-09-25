import logging

from fastapi import FastAPI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("visionguard")

app = FastAPI(title="VisionGuard API")


@app.get("/api/health")
def health():
    logger.info("Health check called")
    return {"status": "ok"}