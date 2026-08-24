from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.entities import Asset, GenerationTask, Project
from app.services import algorithms
from app.services.storage import image_meta, path_to_url, project_root, resolve_project_path


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def latest_image_dir(base: Path) -> Path:
    candidates = [base]
    if base.exists():
        candidates.extend([p for p in base.iterdir() if p.is_dir()])
    candidates = [p for p in candidates if algorithms.list_image_files(p)]
    if not candidates:
        return base
    return max(candidates, key=lambda p: p.stat().st_mtime)


def update_task(db: Session, task: GenerationTask, **values):
    for key, value in values.items():
        setattr(task, key, value)
    task.updated_at = utcnow()
    db.add(task)
    db.commit()
    db.refresh(task)


def add_asset(db: Session, project_id: str, asset_type: str, path: Path, original_name: str | None = None, meta: dict | None = None):
    asset_meta = dict(meta or {})
    if path.is_dir():
        asset_meta["directory_url"] = path_to_url(path)
        preview_path = asset_meta.get("preview_path")
        if preview_path and Path(preview_path).exists():
            asset_meta["url"] = path_to_url(preview_path)
    else:
        asset_meta["url"] = path_to_url(path)
        asset_meta.update(image_meta(path))
    asset = Asset(
        project_id=project_id,
        asset_type=asset_type,
        original_name=original_name or path.name,
        file_path=str(path),
        mime_type=None,
        size_bytes=path.stat().st_size if path.is_file() else 0,
        meta=asset_meta,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


def get_asset(db: Session, asset_id: str) -> Asset:
    asset = db.get(Asset, asset_id)
    if asset is None:
        raise ValueError(f"Asset not found: {asset_id}")
    return asset


def run_task(task_id: str):
    db = SessionLocal()
    task = db.get(GenerationTask, task_id)
    if task is None:
        db.close()
        raise ValueError(f"Task not found: {task_id}")

    try:
        update_task(db, task, status="running", progress=5, message="任务开始", started_at=utcnow())
        params = task.params or {}
        root = project_root(task.project_id)

        if task.task_type == "extract_edge_masks":
            input_asset = get_asset(db, params["asset_id"])
            output_dir = resolve_project_path(task.project_id, "masks", task.id)
            saved = algorithms.extract_edge_masks(
                Path(input_asset.file_path),
                output_dir,
                min_area=int(params.get("min_area", 5000)),
                dilation_size=int(params.get("dilation_size", 3)),
            )
            for path in saved:
                add_asset(db, task.project_id, "mask", path, meta={"task_id": task.id, "source_asset_id": input_asset.id})
            result = {"count": len(saved), "output_dir": str(output_dir)}
            update_task(db, task, status="succeeded", progress=100, message=f"提取 {len(saved)} 个 mask", result=result, finished_at=utcnow())

        elif task.task_type == "extract_gen_masks":
            input_asset = get_asset(db, params["asset_id"])
            output_dir = resolve_project_path(task.project_id, "masks", task.id)
            saved = algorithms.extract_gen_masks(
                Path(input_asset.file_path),
                output_dir,
                scale=float(params.get("scale", 5.0)),
                padding=int(params.get("padding", 20)),
                min_width_mm=float(params.get("min_width_mm", 10.0)),
                min_height_mm=float(params.get("min_height_mm", 10.0)),
                min_area_mm2=float(params.get("min_area_mm2", 100.0)),
                max_aspect_ratio=float(params.get("max_aspect_ratio", 20.0)),
            )
            for path in saved:
                add_asset(db, task.project_id, "mask", path, meta={"task_id": task.id, "source_asset_id": input_asset.id})
            result = {"count": len(saved), "output_dir": str(output_dir)}
            update_task(db, task, status="succeeded", progress=100, message=f"从 GEN 提取 {len(saved)} 个 mask", result=result, finished_at=utcnow())

        elif task.task_type == "extract_redline_masks":
            input_asset = get_asset(db, params["asset_id"])
            output_dir = resolve_project_path(task.project_id, "masks", task.id)
            saved = algorithms.extract_redline_masks(
                Path(input_asset.file_path),
                output_dir,
                min_area=int(params.get("min_area", 3000)),
                dilation_size=int(params.get("dilation_size", 5)),
                dilation_iterations=int(params.get("dilation_iterations", 2)),
            )
            for path in saved:
                add_asset(db, task.project_id, "mask", path, meta={"task_id": task.id, "source_asset_id": input_asset.id})
            result = {"count": len(saved), "output_dir": str(output_dir)}
            update_task(db, task, status="succeeded", progress=100, message=f"提取 {len(saved)} 个 mask", result=result, finished_at=utcnow())

        elif task.task_type == "masks_to_parts":
            project = db.get(Project, task.project_id)
            if project is None:
                raise ValueError(f"Project not found: {task.project_id}")
            texture_asset = get_asset(db, params["texture_asset_id"])
            output_dir = resolve_project_path(task.project_id, "parts", task.id)
            mask_asset_ids = params.get("mask_asset_ids") or []
            if mask_asset_ids:
                mask_assets = [get_asset(db, asset_id) for asset_id in mask_asset_ids]
                mask_files = [Path(asset.file_path) for asset in mask_assets if asset.asset_type == "mask"]
                if not mask_files:
                    raise ValueError("No selected mask assets were found")
                saved = algorithms.texture_mask_files(
                    mask_files,
                    Path(texture_asset.file_path),
                    output_dir,
                    random_crop=bool(params.get("random_crop", True)),
                    max_side_pixels=int(params.get("max_side_pixels", 1000)),
                    project_name=project.name,
                )
            else:
                mask_dir = Path(params["mask_dir"]) if params.get("mask_dir") else latest_image_dir(root / "masks")
                saved = algorithms.texture_masks(
                    mask_dir,
                    Path(texture_asset.file_path),
                    output_dir,
                    random_crop=bool(params.get("random_crop", True)),
                    max_side_pixels=int(params.get("max_side_pixels", 1000)),
                    project_name=project.name,
                )
            for path in saved:
                add_asset(db, task.project_id, "part", path, meta={"task_id": task.id, "texture_asset_id": texture_asset.id, "selected_mask_count": len(mask_asset_ids)})
            result = {"count": len(saved), "output_dir": str(output_dir)}
            update_task(db, task, status="succeeded", progress=100, message=f"生成 {len(saved)} 个透明零件", result=result, finished_at=utcnow())

        elif task.task_type == "generate_dataset":
            project = db.get(Project, task.project_id)
            if project is None:
                raise ValueError(f"Project not found: {task.project_id}")
            background_asset = get_asset(db, params["background_asset_id"])
            parts_dir = Path(params["parts_dir"]) if params.get("parts_dir") else latest_image_dir(root / "parts")
            part_asset_ids = params.get("part_asset_ids") or []
            selected_part_files: list[Path] | None = None
            if part_asset_ids:
                selected_parts = [get_asset(db, asset_id) for asset_id in part_asset_ids]
                selected_part_files = [Path(asset.file_path) for asset in selected_parts if asset.asset_type == "part"]
                if not selected_part_files:
                    raise ValueError("No selected part assets were found")
            output_dir = resolve_project_path(task.project_id, "synthetic", task.id)
            last_reported_progress = 5

            def report_progress(percent: int, message: str):
                nonlocal last_reported_progress
                # Persist only when the visible percentage changes. Updating PostgreSQL
                # once per generated image becomes expensive for large batches.
                if percent <= last_reported_progress:
                    return
                last_reported_progress = percent
                update_task(db, task, progress=percent, message=message)

            result = algorithms.generate_dataset(
                parts_dir=parts_dir,
                part_files=selected_part_files,
                background_path=Path(background_asset.file_path),
                output_dir=output_dir,
                num_images=int(params.get("num_images", 20)),
                min_parts=int(params.get("min_parts", 2)),
                max_parts=int(params.get("max_parts", 8)),
                label_format=str(params.get("label_format", "yolo_hbb")),
                layout_mode=str(params.get("layout_mode", "random")),
                angle_min=float(params.get("angle_min", 0)),
                angle_max=float(params.get("angle_max", 90)),
                scale_min=float(params.get("scale_min", 0.6)),
                scale_max=float(params.get("scale_max", 1.0)),
                margin_top=int(params.get("margin_top", 100)),
                margin_bottom=int(params.get("margin_bottom", 150)),
                margin_left=int(params.get("margin_left", 0)),
                margin_right=int(params.get("margin_right", 0)),
                class_id=int(params.get("class_id", 0)),
                class_name=str(params.get("class_name", "steel_part")),
                jpeg_quality=int(params.get("jpeg_quality", 95)),
                project_name=project.name,
                generation_date=(task.created_at or utcnow()).astimezone(ZoneInfo("Asia/Shanghai")).strftime("%Y%m%d_%H%M%S")
                + f"_{task.id[:8]}",
                progress_callback=report_progress,
            )
            preview_path = result.get("first_image_path")
            if preview_path:
                result["preview_url"] = path_to_url(preview_path)
            add_asset(
                db,
                task.project_id,
                "dataset",
                output_dir,
                original_name=output_dir.name,
                meta={"task_id": task.id, "preview_path": preview_path, **result},
            )
            update_task(db, task, status="succeeded", progress=100, message="数据集生成完成", result=result, finished_at=utcnow())

        else:
            raise ValueError(f"Unsupported task type: {task.task_type}")
    except Exception as exc:
        update_task(db, task, status="failed", progress=100, message="任务失败", error=str(exc), finished_at=utcnow())
        raise
    finally:
        db.close()
