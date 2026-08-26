from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.core.config import settings
from app.api import workspaces, documents, chat

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("docmind")

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response
import json
import re

class JSONControlCharMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            if "application/json" in content_type:
                try:
                    body_bytes = await request.body()
                    if body_bytes:
                        try:
                            json.loads(body_bytes)
                        except json.JSONDecodeError as e:
                            if "control character" in str(e).lower() or "control" in str(e).lower():
                                decoded = body_bytes.decode("utf-8", errors="replace")
                                # Replace raw unescaped control characters (\n, \r, \t) with JSON escape sequences
                                sanitized = re.sub(
                                    r'[\x00-\x1f]',
                                    lambda m: '\\n' if m.group(0) == '\n' else ('\\r' if m.group(0) == '\r' else ('\\t' if m.group(0) == '\t' else '')),
                                    decoded
                                )
                                async def receive():
                                    return {"type": "http.request", "body": sanitized.encode("utf-8")}
                                request._receive = receive
                except Exception as ex:
                    logger.warning(f"JSONControlCharMiddleware exception: {ex}")

        response = await call_next(request)
        return response

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc"
)

app.add_middleware(JSONControlCharMiddleware)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API V1 Routers
app.include_router(workspaces.router, prefix=settings.API_V1_STR)
app.include_router(documents.router, prefix=settings.API_V1_STR)
app.include_router(chat.router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "message": "Welcome to DocMind AI API — Multimodal Evidence-Grounded PDF Intelligence",
        "docs": "/api/v1/docs",
        "version": settings.VERSION
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "docmind-ai-backend"}
