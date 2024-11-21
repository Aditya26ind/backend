from fastapi import FastAPI, Request
from app.routers import auth, documents, queries
import logging
from app.database import Base, engine
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

# Initialize database (for development; use Alembic in production)
Base.metadata.create_all(bind=engine)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Replace with your frontend's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(queries.router)

# Root/Health Check Endpoint
@app.get("/")
async def health_check():
    try:
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        return {"message": "Backend is running!", "status": "healthy"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"message": "Backend is running!", "status": "unhealthy", "error": str(e)}

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# # Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    #check
    # Log request body if it's not binary
    if request.headers.get("content-type") and "multipart/form-data" not in request.headers.get("content-type"):
        try:
            body = await request.body()
            logger.info(f"Request Body: {body.decode('utf-8')}")
        except UnicodeDecodeError:
            logger.warning("Request body contains binary data and could not be decoded.")
    else:
        logger.info("Request contains file upload or binary data.")

    response = await call_next(request)
    logger.info(f"Response: {response.status_code}")
    return response