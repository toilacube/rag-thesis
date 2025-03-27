from fastapi import Request, FastAPI, HTTPException
from fastapi.responses import JSONResponse
import logging

# Initialize logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def register_error_handlers(app: FastAPI):
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled error: {str(exc)} - URL: {request.url}")
        return JSONResponse(
            status_code = exc.status_code,
            content = {
                "status": "error",
                "code": exc.status_code,
                "message": exc.detail
                },
    )