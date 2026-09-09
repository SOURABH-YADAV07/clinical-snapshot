"""FastAPI app entrypoint: CORS, routers, and global exception handlers so
no endpoint ever returns an unstructured 500."""

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.bundles import router as bundles_router
from app.api.patients import router as patients_router

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Clinical Snapshot API",
    description="API for the Clinical Snapshot assessment",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(patients_router)
app.include_router(bundles_router)


@app.exception_handler(FileNotFoundError)
def handle_no_bundle_files(request: Request, exc: FileNotFoundError) -> JSONResponse:
    # Raised by services.loader.load_fhir_bundle() when raw_data/ has no
    # .json files at all (e.g. a fresh checkout, or the demo file was
    # removed) — an operational/config problem, not a bug in the request,
    # so a clean 503 with a clear cause beats an unhandled 500.
    return JSONResponse(
        status_code=503,
        content={"detail": "No FHIR Bundle files found in raw_data/. Restore the original bundle or upload one."},
    )


@app.exception_handler(OSError)
def handle_storage_error(request: Request, exc: OSError) -> JSONResponse:
    # Broader than FileNotFoundError above (which still wins for that exact
    # case — Starlette dispatches to the most specific registered handler):
    # covers permission errors, a full disk, or a read-only filesystem when
    # reading raw_data/ or writing an uploaded Bundle. The client doesn't
    # need the raw OS error text; the server log has it.
    logger.error("Storage error handling %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=503,
        content={"detail": "A storage error occurred handling this request. Check server logs."},
    )


@app.exception_handler(Exception)
def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    # Last-resort safety net: no endpoint should ever return Starlette's
    # bare, unstructured "Internal Server Error" for a genuinely unexpected
    # bug. Logs the full exception server-side; the client gets a clean,
    # generic message with no internal details (stack trace, file paths).
    logger.error("Unhandled error on %s %s", request.method, request.url.path, exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred."},
    )


@app.get("/")
def root():
    return {"message": "Clinical Snapshot API is running"}
