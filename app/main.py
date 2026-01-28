from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

from fastapi.staticfiles import StaticFiles
import os

# Create saved_audits directory if it doesn't exist (it should be created by the service, but good to be safe)
os.makedirs("saved_audits", exist_ok=True)

# Mount static files
app.mount("/static/saved_audits", StaticFiles(directory="saved_audits"), name="saved_audits")

@app.get("/")
async def root():
    return {"message": "Welcome to the Embeddings Optimization API", "docs": "/docs"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
