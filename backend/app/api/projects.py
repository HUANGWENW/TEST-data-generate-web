from pathlib import Path
import tempfile
from typing import Literal
import zipfile

import redis
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from rq import Queue
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.background import BackgroundTask

from app.core.config import get_settings
from app.core.database import get_db
from app.models.entities import Asset, GenerationTask, Project
from app.schemas.entities import AssetRead, DatasetGalleryRead, ProjectCreate, ProjectRead, TaskCreate, TaskRead
from app.services.storage import image_meta, path_to_url, project_root, safe_name, save_upload_file
from app.workers.jobs import run_task

router = APIRouter(prefix="/projects", tags=["projects"])

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}


@router.post("", response_model=ProjectRead)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    project = Project(name=payload.name, description=payload.description)
    db.add(project)
    db.commit()
    db.refresh(project)
    project_root(project.id)
    return project


@router.get("", response_model=list[ProjectRead])
def list_projects(db: Session = Depends(get_db)):
    return db.scalars(select(Project).order_by(Project.created_at.desc())).all()


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: str, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("/{project_id}/assets/upload", response_model=AssetRead)
def upload_asset(
    project_id: str,
    asset_type: str = Query(default="input"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if db.get(Project, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if asset_type == "dxf" and Path(file.filename or "").suffix.lower() != ".dxf":
        raise HTTPException(status_code=422, detail="DXF upload requires a .dxf file")
    path = save_upload_file(project_id, asset_type, file)
    meta = {"url": path_to_url(path), **image_meta(path)}
    if asset_type == "dxf":
        meta["parse_status"] = "pending"
    asset = Asset(
        project_id=project_id,
        asset_type=asset_type,
        original_name=file.filename or Path(path).name,
        file_path=str(path),
        mime_type=file.content_type,
        size_bytes=path.stat().st_size,
        meta=meta,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


@router.get("/{project_id}/assets", response_model=list[AssetRead])
def list_assets(project_id: str, asset_type: str | None = None, db: Session = Depends(get_db)):
    stmt = select(Asset).where(Asset.project_id == project_id)
    if asset_type:
        stmt = stmt.where(Asset.asset_type == asset_type)
    assets = db.scalars(stmt.order_by(Asset.created_at.desc())).all()
    changed = False
    for asset in assets:
        if asset.file_path and not asset.meta.get("width"):
            meta = image_meta(asset.file_path)
            if meta:
                asset.meta = {**asset.meta, **meta}
                db.add(asset)
                changed = True
    if changed:
        db.commit()
        for asset in assets:
            db.refresh(asset)
    return assets


@router.get("/{project_id}/datasets/{dataset_id}/files", response_model=DatasetGalleryRead)
def list_dataset_files(project_id: str, dataset_id: str, db: Session = Depends(get_db)):
    dataset = db.get(Asset, dataset_id)
    if dataset is None or dataset.project_id != project_id or dataset.asset_type != "dataset":
        raise HTTPException(status_code=404, detail="Dataset not found")

    root = project_root(project_id).resolve()
    output_dir = Path(dataset.file_path).resolve()
    if output_dir != root and root not in output_dir.parents:
        raise HTTPException(status_code=400, detail="Dataset path is invalid")

    images_dir = output_dir / "images"
    labels_dir = output_dir / "labels"
    metadata_dir = output_dir / "metadata"
    image_paths = sorted((path for path in images_dir.glob("*") if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES), key=lambda path: path.name)
    files = []
    for image_path in image_paths:
        base_name = image_path.stem
        label_path = labels_dir / f"{base_name}.txt"
        metadata_path = metadata_dir / f"{base_name}.txt"
        files.append({
            "file_name": image_path.name,
            "image_url": path_to_url(image_path),
            "label_url": path_to_url(label_path) if label_path.exists() else None,
            "metadata_url": path_to_url(metadata_path) if metadata_path.exists() else None,
        })

    meta = dataset.meta or {}
    return {
        "dataset_id": dataset.id,
        "name": dataset.original_name,
        "created_at": dataset.created_at,
        "label_format": meta.get("label_format"),
        "layout_mode": meta.get("layout_mode"),
        "total_images": len(files),
        "files": files,
    }


@router.get("/{project_id}/datasets/{dataset_id}/download")
def download_dataset_archive(
    project_id: str,
    dataset_id: str,
    content: Literal["images", "labels", "all"] = Query(default="all"),
    db: Session = Depends(get_db),
):
    project = db.get(Project, project_id)
    dataset = db.get(Asset, dataset_id)
    if project is None or dataset is None or dataset.project_id != project_id or dataset.asset_type != "dataset":
        raise HTTPException(status_code=404, detail="Dataset not found")

    root = project_root(project_id).resolve()
    output_dir = Path(dataset.file_path).resolve()
    if output_dir != root and root not in output_dir.parents:
        raise HTTPException(status_code=400, detail="Dataset path is invalid")

    archive_entries: list[tuple[Path, str]] = []
    if content in {"images", "all"}:
        images_dir = output_dir / "images"
        archive_entries.extend(
            (path, f"images/{path.name}")
            for path in sorted(images_dir.glob("*"), key=lambda item: item.name)
            if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
        )
    if content in {"labels", "all"}:
        labels_dir = output_dir / "labels"
        archive_entries.extend(
            (path, f"labels/{path.name}")
            for path in sorted(labels_dir.glob("*"), key=lambda item: item.name)
            if path.is_file() and path.suffix.lower() == ".txt"
        )
    if not archive_entries:
        raise HTTPException(status_code=404, detail="No matching files found in dataset")

    temporary_archive = tempfile.NamedTemporaryFile(prefix="dataset_", suffix=".zip", delete=False)
    archive_path = Path(temporary_archive.name)
    temporary_archive.close()
    try:
        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_STORED, allowZip64=True) as archive:
            for source_path, archive_name in archive_entries:
                compression = zipfile.ZIP_DEFLATED if source_path.suffix.lower() == ".txt" else zipfile.ZIP_STORED
                archive.write(source_path, archive_name, compress_type=compression)
    except Exception:
        archive_path.unlink(missing_ok=True)
        raise

    content_labels = {"images": "images", "labels": "labels", "all": "images_labels"}
    archive_name = f"{safe_name(project.name)}_{dataset.created_at:%Y%m%d}_{content_labels[content]}.zip"
    return FileResponse(
        archive_path,
        media_type="application/zip",
        filename=archive_name,
        background=BackgroundTask(archive_path.unlink, missing_ok=True),
    )


@router.post("/{project_id}/tasks", response_model=TaskRead)
def create_task(project_id: str, payload: TaskCreate, db: Session = Depends(get_db)):
    if db.get(Project, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    task = GenerationTask(project_id=project_id, task_type=payload.task_type, params=payload.params, status="queued", progress=0, message="等待执行")
    db.add(task)
    db.commit()
    db.refresh(task)

    settings = get_settings()
    connection = redis.from_url(settings.redis_url)
    queue = Queue("default", connection=connection)
    job = queue.enqueue(run_task, task.id, job_timeout="2h")
    task.rq_job_id = job.id
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("/{project_id}/tasks", response_model=list[TaskRead])
def list_project_tasks(project_id: str, db: Session = Depends(get_db)):
    stmt = select(GenerationTask).where(GenerationTask.project_id == project_id).order_by(GenerationTask.created_at.desc())
    return db.scalars(stmt).all()
