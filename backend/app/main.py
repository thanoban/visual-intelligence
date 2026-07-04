from contextlib import asynccontextmanager

from fastapi import FastAPI

from .api.router import api_router
from .db import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="VisualSprint API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    app.include_router(api_router)
    return app


app = create_app()
