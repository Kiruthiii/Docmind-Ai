import asyncio
import json
import logging
import re

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

from app.api import chat, documents, workspaces
from app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("docmind")


def _sanitize_json_str(text: str) -> str:
    """CPU-bound regex sanitization executed off the main asyncio event loop."""
    return re.sub(
        r'[\x00-\x1f]',
        lambda m: '\\n' if m.group(0) == '\n' else ('\\r' if m.group(0) == '\r' else ('\\t' if m.group(0) == '\t' else f'\\u{ord(m.group(0)):04x}')),
        text
    )


class NonBlockingJSONControlCharMiddleware:
    """
    Pure ASGI middleware that handles raw unescaped JSON control characters without event-loop blocking:
    1. Uses C-accelerated json.loads(..., strict=False) for zero-overhead fast-path parsing.
    2. Offloads CPU-bound regex sanitization to worker threads via asyncio.to_thread.
    """
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "")
        if method in ("POST", "PUT", "PATCH"):
            headers = dict(scope.get("headers", []))
            content_type = headers.get(b"content-type", b"").decode("latin-1")
            if "application/json" in content_type:
                body_bytes = bytearray()
                more_body = True
                while more_body:
                    message = await receive()
                    if message["type"] == "http.request":
                        body_bytes.extend(message.get("body", b""))
                        more_body = message.get("more_body", False)

                if body_bytes:
                    try:
                        # Fast path: C-accelerated non-strict parsing allows unescaped control chars (\n, \r, \t) without regex
                        json.loads(body_bytes, strict=False)
                    except json.JSONDecodeError:
                        # Slow path: Offload CPU-bound regex sanitization off the asyncio event loop
                        try:
                            decoded = body_bytes.decode("utf-8", errors="replace")
                            sanitized = await asyncio.to_thread(_sanitize_json_str, decoded)
                            body_bytes = bytearray(sanitized.encode("utf-8"))
                        except Exception as ex:
                            logger.warning(f"JSON control char sanitization failed: {ex}")

                body_sent = False

                async def custom_receive() -> dict:
                    nonlocal body_sent
                    if not body_sent:
                        body_sent = True
                        return {
                            "type": "http.request",
                            "body": bytes(body_bytes),
                            "more_body": False,
                        }
                    return await receive()

                await self.app(scope, custom_receive, send)
                return

        await self.app(scope, receive, send)


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc"
)

app.add_middleware(NonBlockingJSONControlCharMiddleware)

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
