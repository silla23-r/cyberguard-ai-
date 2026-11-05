"""
Main Entrypoint for CyberGuard AI Backend Server.
Runs FastAPI with CORS, WebSocket support, and static file hosting.
"""
import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from config import settings
from api.routes import router as api_router
from api.websocket import router as ws_router
from api.whatsapp_routes import router as whatsapp_router
from api.security_middleware import SecurityRateLimitMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("CyberGuard")

app = FastAPI(
    title="CyberGuard AI — Multimodal Fraud Defense Agent",
    description="Real-time multi-agent defense system for financial scams, UPI fraud, and digital arrest intimidation.",
    version="1.0.0"
)

# Enterprise Security & Rate Limiting Middleware
app.add_middleware(SecurityRateLimitMiddleware)

# CORS Middleware - Permissive for all Vercel deployments and mobile clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(api_router)
app.include_router(ws_router)
app.include_router(whatsapp_router)

# Mount Static Folders
app.mount("/static", StaticFiles(directory=str(settings.STATIC_DIR)), name="static")

@app.get("/")
async def root():
    """Serves the built-in standalone UI dashboard if present, or health info."""
    index_file = settings.STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {
        "service": "CyberGuard AI Agent Backend",
        "status": "online",
        "docs_url": "/docs"
    }

if __name__ == "__main__":
    import sys
    import uvicorn
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(f"[+] Starting CyberGuard AI Server on http://{settings.HOST}:{settings.PORT}")
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)

