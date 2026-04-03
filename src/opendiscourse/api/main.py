"""FastAPI application for OpenDiscourse."""

from contextlib import asynccontextmanager
from fastapi import FastAPI

from opendiscourse.database import close_db, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await close_db()


app = FastAPI(
    title="OpenDiscourse",
    description="US Government Data Aggregation API",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "opendiscourse"}


@app.get("/")
async def root():
    return {
        "name": "OpenDiscourse",
        "version": "0.1.0",
        "docs": "/docs",
    }
