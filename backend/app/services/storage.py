from __future__ import annotations

import re
import shutil
import uuid
from pathlib import Path

import cv2
from fastapi import UploadFile

from app.core.config import get_settings


PROJECT_DIRS = [
    "uploads",
    "dxfs",
    "masks",
    "parts",
    "backgrounds",
    "textures",
    "synthetic/images",
    "synthetic/labels",
    "synthetic/annotations",
    "synthetic/metadata",
    "previews",
    "exports",
]


def safe_name(filename: str) -> str:
    name = Path(filename).name
    return re.sub(r"[^A-Za-z0-9._\-\u4e00-\u9fff]+", "_", name).strip("._") or "file"


def storage_root() -> Path:
    root = get_settings().storage_root
    root.mkdir(parents=True, exist_ok=True)
    return root


def project_root(project_id: str) -> Path:
    root = storage_root() / "projects" / project_id
    for rel in PROJECT_DIRS:
        (root / rel).mkdir(parents=True, exist_ok=True)
    return root


def resolve_project_path(project_id: str, *parts: str) -> Path:
    root = project_root(project_id).resolve()
    path = (root / Path(*parts)).resolve()
    if root != path and root not in path.parents:
        raise ValueError("Path escapes project storage")
    return path


def save_upload_file(project_id: str, asset_type: str, upload: UploadFile) -> Path:
    filename = safe_name(upload.filename or "upload.bin")
    directory_by_type = {"input": "uploads", "dxf": "dxfs"}
    target_dir = project_root(project_id) / directory_by_type.get(asset_type, asset_type + "s")
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{uuid.uuid4().hex}_{filename}"
    with target.open("wb") as dst:
        shutil.copyfileobj(upload.file, dst)
    return target


def image_meta(path: str | Path) -> dict:
    image_path = Path(path)
    if image_path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}:
        return {}
    image = cv2.imread(str(image_path), cv2.IMREAD_UNCHANGED)
    if image is None:
        return {}
    height, width = image.shape[:2]
    channels = 1 if image.ndim == 2 else image.shape[2]
    return {"width": int(width), "height": int(height), "channels": int(channels)}


def path_to_url(path: str | Path) -> str:
    root = storage_root().resolve()
    resolved = Path(path).resolve()
    rel = resolved.relative_to(root)
    return "/storage/" + rel.as_posix()
