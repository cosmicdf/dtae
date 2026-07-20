from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routes import assemble, health, tools, usage


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup: nothing blocking required — registry starts empty, tools added via API
    yield
    # Shutdown: flush any pending state here if persistence is added later


app = FastAPI(
    title="DTAE API",
    description="Dynamic Tool Assembly Engine — REST API for tool registry and just-in-time assembly",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(tools.router)
app.include_router(assemble.router)
app.include_router(usage.router)
