from fastapi import APIRouter, FastAPI
import sqlalchemy
from app.core.api_reponse import api_response
from app.core.exception_handler import register_error_handlers
from app.api.api import main_router
from app.config.config import config
import os

app = FastAPI()
db = sqlalchemy

register_error_handlers(app)

app.include_router(main_router, prefix="/api")

@app.get("/api/health")
async def health_check():
    return {
        "status": "UP",
    } 

@app.get("/")
async def root():
    return api_response(
        data = {
            "message": "Welcome to the FastAPI application!"
        },
        message = "Root endpoint"
    )