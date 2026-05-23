from __future__ import annotations

from importlib import resources

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, Response

router = APIRouter()
_ASSETS = resources.files("qcflows_api.demo")


@router.get("/", response_class=HTMLResponse)
def demo_page() -> HTMLResponse:
    return HTMLResponse(_read_asset("index.html"))


@router.get("/demo.css", include_in_schema=False)
def demo_styles() -> Response:
    return Response(
        _read_asset("demo.css"),
        media_type="text/css",
    )


@router.get("/demo.js", include_in_schema=False)
def demo_script() -> Response:
    return Response(
        _read_asset("demo.js"),
        media_type="application/javascript",
    )


def _read_asset(filename: str) -> str:
    return _ASSETS.joinpath(filename).read_text(encoding="utf-8")
