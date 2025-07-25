"""
ACME Transactions System - FastAPI application entrypoint.

- Mounts the API router for all reporting endpoints.
- Provides a root health check endpoint.
- Designed for use with Uvicorn in Docker Compose.
"""

from fastapi import FastAPI
from api import router

app = FastAPI()
"""The main FastAPI application instance. All API endpoints are mounted here."""
app.include_router(router)

@app.get("/")
def root():
    """
    Health check endpoint.
    Returns a welcome message to confirm the API is running.
    """
    return {"message": "ACME Transactions API"} 