"""
api.py – FastAPI web interface for portmanteau_power.

Install the optional dependency first::

    pip install "portmanteau-power[api]"

Run the server::

    uvicorn portmanteau_power.api:app --reload --port 8000

Or via the helper entry point::

    python -m portmanteau_power.api

Endpoints
---------
POST /generate
    Generate names from a list of seed words.

GET  /themes
    List available theme names.

GET  /health
    Liveness check.
"""

from __future__ import annotations

import sys
from typing import Any, Dict, List, Optional

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel, Field
    _FASTAPI_OK = True
except ImportError:
    _FASTAPI_OK = False

from portmanteau_power import __version__
from portmanteau_power.config import load_config, apply_cli_overrides, DEFAULT_CONFIG
from portmanteau_power.generator import generate
from portmanteau_power.themes import ALL_THEME_NAMES


def _require_fastapi() -> None:
    if not _FASTAPI_OK:
        raise RuntimeError(
            "FastAPI is not installed.  "
            'Run: pip install "portmanteau-power[api]"'
        )


# ---------------------------------------------------------------------------
# Request / Response models (defined unconditionally so imports always work)
# ---------------------------------------------------------------------------

if _FASTAPI_OK:
    class GenerateRequest(BaseModel):
        words: List[str] = Field(
            ...,
            min_length=1,
            description="Seed words to generate names from.",
            examples=[["power", "nova", "forge"]],
        )
        target_size: int = Field(
            100,
            ge=1,
            le=10000,
            description="Maximum number of names to return.",
        )
        themes: Optional[List[str]] = Field(
            None,
            description="Theme names to activate (null = use defaults).",
        )
        min_len: Optional[int] = Field(None, ge=3, le=30)
        max_len: Optional[int] = Field(None, ge=3, le=50)
        allow_triples: bool = Field(
            False,
            description="Enable triple-blend generation (slower).",
        )
        banned_substrings: Optional[List[str]] = Field(None)
        include_scores: bool = Field(
            False,
            description="Include score breakdown in response.",
        )
        safe_international: bool = Field(
            False,
            description="Filter names that are offensive in other languages.",
        )
        config: Optional[Dict[str, Any]] = Field(
            None,
            description="Raw config dict (deep-merged over defaults).",
        )

    class NameEntry(BaseModel):
        name: str
        score: Optional[float] = None
        breakdown: Optional[Dict[str, float]] = None
        components: Optional[List[str]] = None
        join_strategy: Optional[str] = None

    class GenerateResponse(BaseModel):
        version: str
        count: int
        names: List[NameEntry]

else:
    # Placeholders so the module can be imported even without fastapi
    GenerateRequest = None  # type: ignore[assignment,misc]
    GenerateResponse = None  # type: ignore[assignment,misc]
    NameEntry = None  # type: ignore[assignment,misc]


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

if _FASTAPI_OK:
    app = FastAPI(
        title="portmanteau_power API",
        version=__version__,
        description=(
            "Generate brand-quality portmanteau / invented names from seed words. "
            "See POST /generate for full options."
        ),
    )

    @app.get("/health")
    def health() -> Dict[str, str]:
        return {"status": "ok", "version": __version__}

    @app.get("/themes")
    def list_themes() -> Dict[str, List[str]]:
        return {"themes": list(ALL_THEME_NAMES)}

    @app.post("/generate", response_model=GenerateResponse)
    def generate_names(req: GenerateRequest) -> GenerateResponse:
        # Build config
        cfg = load_config(None)
        if req.config:
            from portmanteau_power.config import _deep_merge
            cfg = _deep_merge(cfg, req.config)

        # Validate and apply theme overrides
        if req.themes is not None:
            unknown = [t for t in req.themes if t not in ALL_THEME_NAMES]
            if unknown:
                raise HTTPException(
                    status_code=422,
                    detail=f"Unknown themes: {unknown}. Available: {ALL_THEME_NAMES}",
                )

        try:
            cfg = apply_cli_overrides(
                cfg,
                target_size=req.target_size,
                min_len=req.min_len,
                max_len=req.max_len,
                themes=req.themes,
                allow_triples=req.allow_triples or None,
                banned_substrings=req.banned_substrings,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))

        # Safe-international filter
        if req.safe_international:
            cfg["features"] = cfg.get("features", {})
            cfg["features"]["safe_international"] = True

        results = generate(req.words, cfg, target_size=req.target_size)

        entries = []
        for c in results:
            entry = NameEntry(name=c.text)
            if req.include_scores:
                entry.score = round(c.score, 6)
                entry.breakdown = c.score_breakdown
                entry.components = c.components
                entry.join_strategy = c.join_strategy
            entries.append(entry)

        return GenerateResponse(
            version=__version__,
            count=len(entries),
            names=entries,
        )

else:
    app = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Module-level runnable
# ---------------------------------------------------------------------------

def _serve(host: str = "127.0.0.1", port: int = 8000) -> None:
    _require_fastapi()
    try:
        import uvicorn  # type: ignore
    except ImportError:
        raise RuntimeError(
            "uvicorn is not installed.  "
            'Run: pip install "portmanteau-power[api]"'
        )
    uvicorn.run("portmanteau_power.api:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    import argparse

    _require_fastapi()
    ap = argparse.ArgumentParser(description="Start portmanteau_power API server.")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args()
    _serve(host=args.host, port=args.port)
