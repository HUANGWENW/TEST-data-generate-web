from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
import logging
from pathlib import Path
import shutil
import uuid

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.entities import Asset, GenerationTask, Project
from app.services.storage import storage_root

logger = logging.getLogger(__name__)
ACTIVE_STATUSES = ("queued", "running")


def lock_project(db: Session, project_id: str) -> Project:
    """Serialize deletion, uploads and task creation for the same project."""
    project = db.scalar(select(Project).where(Project.id == project_id).with_for_update())
    if project is None:
        raise HTTPException(status_code=404, detail="项目不存在或已被删除")
    return project


def ensure_project_idle(db: Session, project_id: str) -> None:
    active = db.scalar(select(GenerationTask.id).where(
        GenerationTask.project_id == project_id,
        GenerationTask.status.in_(ACTIVE_STATUSES),
    ).limit(1))
    if active is not None:
        raise HTTPException(status_code=409, detail="项目有排队或运行中的任务，请等待任务结束后再删除")


def checked_project_directory(project_id: str) -> Path:
    root = storage_root().resolve()
    projects = root / "projects"
    if projects.is_symlink() or projects.resolve().parent != root:
        raise HTTPException(status_code=409, detail="项目存储路径异常，未执行删除")
    projects = projects.resolve()
    directory = projects / project_id
    if directory.is_symlink() or directory.resolve().parent != projects:
        raise HTTPException(status_code=409, detail="项目存储路径异常，未执行删除")
    return directory


def checked_asset_path(asset: Asset, directory: Path) -> Path:
    path = Path(asset.file_path)
    root = directory.resolve()
    resolved = path.resolve()
    expected = root / ("masks" if asset.asset_type == "mask" else "parts")
    if path.is_symlink() or expected not in resolved.parents or not resolved.is_relative_to(root):
        raise HTTPException(status_code=409, detail="素材存储路径异常，未执行删除")
    if path.exists() and not path.is_file():
        raise HTTPException(status_code=409, detail="素材文件类型异常，未执行删除")
    return path


@contextmanager
def staged_files(paths: list[Path]) -> Iterator[None]:
    """Move files first, restore on database failure, remove after commit.

    A missing file is fine: its stale database record can still be removed.
    Failure to reclaim trash after commit is logged rather than returning a
    misleading failure for a deletion already committed to the database.
    """
    trash_parent = storage_root().resolve() / ".deletions"
    if trash_parent.is_symlink():
        raise OSError("Deletion staging directory must not be a symlink")
    trash_parent.mkdir(exist_ok=True)
    trash = trash_parent / uuid.uuid4().hex
    trash.mkdir()
    moved: list[tuple[Path, Path]] = []
    try:
        for path in dict.fromkeys(paths):
            if path.exists():
                target = trash / str(len(moved))
                path.rename(target)
                moved.append((path, target))
        yield
    except BaseException:
        for original, target in reversed(moved):
            original.parent.mkdir(parents=True, exist_ok=True)
            target.rename(original)
        trash.rmdir()
        raise
    else:
        try:
            shutil.rmtree(trash)
        except OSError:
            logger.exception("Deletion committed; failed to reclaim staging directory %s", trash)


def delete_project_data(db: Session, project_id: str) -> None:
    project = lock_project(db, project_id)
    ensure_project_idle(db, project_id)
    directory = checked_project_directory(project_id)
    try:
        with staged_files([directory]):
            db.delete(project)
            db.commit()
    except (OSError, SQLAlchemyError) as exc:
        db.rollback()
        logger.exception("Could not delete project %s", project_id)
        raise HTTPException(status_code=500, detail="项目删除失败，请检查存储权限或稍后重试") from exc


def delete_asset_data(db: Session, project_id: str, asset_ids: list[str]) -> list[str]:
    lock_project(db, project_id)
    ensure_project_idle(db, project_id)
    ids = list(dict.fromkeys(asset_ids))
    assets = db.scalars(select(Asset).where(Asset.project_id == project_id, Asset.id.in_(ids))).all()
    if len(assets) != len(ids):
        raise HTTPException(status_code=404, detail="部分素材不存在、已被删除或不属于当前项目，请刷新后重试")
    if any(asset.asset_type not in {"mask", "part"} for asset in assets):
        raise HTTPException(status_code=422, detail="此操作仅支持删除 Mask 和透明零件")
    directory = checked_project_directory(project_id)
    paths = {asset.id: checked_asset_path(asset, directory) for asset in assets}
    # If duplicate records refer to one file, keep it for remaining records.
    retained_paths = set(db.scalars(select(Asset.file_path).where(
        Asset.file_path.in_([asset.file_path for asset in assets]), Asset.id.not_in(ids),
    )).all())
    removable = [paths[asset.id] for asset in assets if asset.file_path not in retained_paths]
    try:
        with staged_files(removable):
            for asset in assets:
                db.delete(asset)
            db.commit()
    except (OSError, SQLAlchemyError) as exc:
        db.rollback()
        logger.exception("Could not delete assets from project %s", project_id)
        raise HTTPException(status_code=500, detail="素材删除失败，请检查存储权限或稍后重试") from exc
    return ids
