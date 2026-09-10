import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat, documents, workspaces
from app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("docmind")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc"
)

# Configure production-ready CORS for frontend integrations (including Cloudflare Pages/Workers)
raw_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
use_wildcard = "*" in raw_origins or not raw_origins

if use_wildcard:
    cors_origins = ["*"]
    cors_allow_credentials = False
    cors_origin_regex = None
else:
    cors_origins = raw_origins
    cors_allow_credentials = True
    cors_origin_regex = r"https://.*\.pages\.dev|https://.*\.cloudflare\.com"

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=cors_origin_regex,
    allow_credentials=cors_allow_credentials,
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
