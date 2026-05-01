"""Minimal FastAPI server for connect-config-network module."""
import os
import json
from pathlib import Path

import yaml
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

# Load module manifest
MANIFEST_PATH = Path(__file__).parent.parent / "module.yaml"
manifest = yaml.safe_load(MANIFEST_PATH.read_text()) if MANIFEST_PATH.exists() else {}

MODULE_NAME = manifest.get("name", "unknown-module")
MODULE_ROUTE = manifest.get("route", "/")
PAGES = manifest.get("pages", [])

app = FastAPI(title=MODULE_NAME)

# Serve model files and UI files via dedicated endpoints
@app.get("/api/health")
def health():
    return {"status": "ok", "module": MODULE_NAME}

@app.get("/module.yaml")
def get_manifest():
    if not MANIFEST_PATH.exists():
        raise HTTPException(status_code=404, detail="manifest not found")
    return PlainTextResponse(MANIFEST_PATH.read_text(), media_type="text/yaml")

@app.get("/api/pages")
def list_pages():
    return {"pages": PAGES}

@app.get("/ui/{filename}")
def serve_ui(filename: str):
    ui_dir = Path(__file__).parent.parent / "ui"
    file_path = ui_dir / filename
    if ".." in Path(filename).parts or not file_path.exists():
        raise HTTPException(status_code=404, detail="not found")
    media = "text/typescript" if filename.endswith(".ts") else "text/plain"
    return FileResponse(file_path, media_type=media)

@app.get("/model/{filename}")
def serve_model(filename: str):
    model_dir = Path(__file__).parent.parent / "model"
    file_path = model_dir / filename
    if ".." in Path(filename).parts or not file_path.exists():
        raise HTTPException(status_code=404, detail="not found")
    media = "text/x-python" if filename.endswith(".py") else "text/plain"
    return FileResponse(file_path, media_type=media)

@app.get("/api/models")
def list_models():
    model_dir = Path(__file__).parent.parent / "model"
    files = [f.name for f in model_dir.iterdir() if f.is_file() and f.suffix == ".py"] if model_dir.exists() else []
    return {"models": files}

def _index_html():
    links = "\n".join(
        f'<li><a href="/ui/{p}">{p}</a></li>' for p in PAGES
    )
    return f"""<!doctype html>
<html>
<head><title>{MODULE_NAME}</title></head>
<body>
<h1>{MODULE_NAME}</h1>
<p>Route: <code>{MODULE_ROUTE}</code></p>
<ul>{links}</ul>
<hr>
<a href="/api/health">health</a> |
<a href="/module.yaml">manifest</a> |
<a href="/api/pages">pages</a> |
<a href="/api/models">models</a>
</body>
</html>
"""

@app.get("/")
def index():
    return HTMLResponse(_index_html())

@app.get(MODULE_ROUTE)
def module_index():
    return HTMLResponse(_index_html())

# Mount UI directory for raw file access (optional)
ui_root = Path(__file__).parent.parent / "ui"
if ui_root.exists():
    app.mount("/ui-raw", StaticFiles(directory=str(ui_root)), name="ui_raw")
