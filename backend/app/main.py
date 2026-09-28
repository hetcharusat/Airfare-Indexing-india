import os
import sys

workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.app.config import settings
from backend.app.database import engine, Base
from backend.app.api import routes_indices, routes_scraper, routes_dgca
from backend.app.services.scheduler import scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables exist and start scheduler
    Base.metadata.create_all(bind=engine)
    scheduler.start()
    yield
    # Shutdown: stop scheduler
    scheduler.stop()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Real-Time Airfare Price Index for India (MoSPI / DGCA - SIH26056)",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Include API Routers
app.include_router(routes_indices.router, prefix=settings.API_V1_STR)
app.include_router(routes_scraper.router, prefix=settings.API_V1_STR)
app.include_router(routes_dgca.router, prefix=settings.API_V1_STR)

from src.engine.fisher_engine import fisher_engine

# Mount Static and Vite Assets Files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    assets_dir = os.path.join(static_dir, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Chapter 5.3 Serving Layer Specifications: Dumb API, smart pipeline
@app.get("/index/daily")
def get_spec_daily_indices():
    """Returns daily Fisher, Laspeyres, Paasche, Naive, Bortkiewicz Covariance, and 95% Bootstrap CI."""
    df = fisher_engine.compute_daily_fisher_series()
    return df.to_dict(orient="records")

@app.get("/index/decomposition")
def get_spec_decomposition():
    """Returns overall decomposition and mix shift metrics."""
    df = fisher_engine.compute_daily_fisher_series()
    peak = df.loc[df["divergence_points"].idxmax()].to_dict()
    return {
        "status": "success",
        "description": "Bortkiewicz & Montgomery Decomposition",
        "peak_divergence_event": peak,
        "mean_bortkiewicz_cov": float(df["bortkiewicz_cov"].mean()),
        "time_series_sample": df[["date", "fisher_index", "naive_index", "divergence_points", "bortkiewicz_cov"]].tail(10).to_dict(orient="records")
    }

@app.get("/index/reconciliation")
def get_spec_reconciliation():
    """Validation Protocol: Reconciling with DGCA (Chapter 6 Bridge Series)."""
    return fisher_engine.generate_dgca_reconciliation()

@app.get("/terminal")
@app.get("/mospi")
def mospi_terminal():
    """Serves the official sovereign MoSPI / DGCA Economic Index Terminal."""
    mospi_file = os.path.join(static_dir, "mospi_terminal.html")
    if os.path.exists(mospi_file):
        return FileResponse(mospi_file)
    return FileResponse(os.path.join(static_dir, "index.html"))

@app.get("/")
def root():
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {
        "message": "Project APIx: Economic Price Index Terminal (MoSPI / DGCA)",
        "docs": "/docs",
        "terminal": "/terminal",
        "health": "/api/v1/health"
    }

@app.get(f"{settings.API_V1_STR}/health")
def health_check():
    return {
        "status": "HEALTHY",
        "project": "APIx",
        "organization": "MoSPI / DGCA",
        "database": "CONNECTED",
        "engine": "Laspeyres Fixed-Basket Index"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
