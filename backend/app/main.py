from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import db
from app.config import settings
from app.discord import send_discord_summary
from app.services import current_dashboard, refresh_dashboard


app = FastAPI(title="GOLD Environment Dashboard", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/dashboard/current")
def dashboard_current() -> dict:
    with db.session() as conn:
        return current_dashboard(conn)


@app.post("/api/refresh")
def refresh() -> dict:
    with db.session() as conn:
        return refresh_dashboard(conn)


@app.post("/api/discord/test")
def discord_test() -> dict:
    with db.session() as conn:
        snapshot = current_dashboard(conn)
        return send_discord_summary(conn, snapshot)

