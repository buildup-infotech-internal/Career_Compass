from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import settings

app = FastAPI(
  title=settings.APP_NAME,
  description="AI powered career guidance and job search platform",
  version="1.0.0",
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
def root():
    return {
        "success": True,
        "message": "Welcome to the Career Compass API!"
        }

@app.get("/health")
def health_check():
    return {
        "success": True,
        "message": "API is healthy and running!"
    }  