from fastapi import FastAPI

app = FastAPI(
    title="Clinical Snapshot API",
    description="API for the Clinical Snapshot assessment",
    version="0.1.0",
)


@app.get("/")
def root():
    return {"message": "Clinical Snapshot API is running"}