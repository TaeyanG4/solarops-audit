"""Local-only administrative origin, separate from the read-only dashboard."""

import secrets
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict

from solarops.admin.services import ControlError, ServiceManager


class Action(BaseModel):
    model_config = ConfigDict(extra="forbid")
    target: Literal["workspace", "dashboard", "database", "storage", "airflow", "kubernetes"]
    action: Literal["start", "stop"]
    confirmed: Literal[True]


def create_admin_app(root: Path, manager=None):
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    manager = manager or ServiceManager(root)
    token = secrets.token_urlsafe(32)
    assets = Path(__file__).parent.parent / "api"
    app.mount("/static", StaticFiles(directory=assets / "static"), name="static")

    @app.middleware("http")
    async def local_only(request: Request, call_next):
        # Exact Host defeats DNS rebinding; Origin + token defeat cross-site mutations.
        origin = "http://127.0.0.1:8504"
        if (
            request.headers.get("host") != "127.0.0.1:8504"
            or request.client is None
            or request.client.host not in {"127.0.0.1", "::1"}
            or request.headers.get("origin", origin) != origin
            or (
                request.url.path.startswith("/api/")
                and request.headers.get("sec-fetch-site", "none") not in {"same-origin", "none"}
            )
        ):
            return JSONResponse(
                {"detail": "로컬 관리 화면에서만 접근할 수 있습니다."}, status_code=403
            )
        if request.method not in {"GET", "HEAD"} and (
            request.headers.get("origin") != origin
            or not secrets.compare_digest(request.headers.get("x-solarops-token", ""), token)
        ):
            return JSONResponse(
                {"detail": "관리 화면을 새로고침한 뒤 다시 시도하세요."}, status_code=403
            )
        response = await call_next(request)
        response.headers.update(
            {
                "Cache-Control": "no-store",
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
                "Referrer-Policy": "no-referrer",
                "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; font-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'",
            }
        )
        return response

    @app.get("/")
    def page():
        return FileResponse(Path(__file__).with_name("index.html"))

    @app.get("/api/admin/session")
    def session():
        return {"token": token}

    @app.get("/api/admin/status")
    def status():
        return manager.status()

    @app.post("/api/admin/actions", status_code=202)
    def action(body: Action):
        try:
            return manager.submit(body.target, body.action)
        except ControlError as exc:
            raise HTTPException(409, str(exc)) from exc

    return app
