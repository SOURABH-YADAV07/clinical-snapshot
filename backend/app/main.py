from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.patients import router as patients_router

app = FastAPI(
    title="Clinical Snapshot API",
    description="API for the Clinical Snapshot assessment",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(patients_router)


@app.get("/")
def root():
    return {"message": "Clinical Snapshot API is running"}
