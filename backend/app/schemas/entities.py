from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    description: str | None = None


class ProjectRead(BaseModel):
    id: str
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AssetRead(BaseModel):
    id: str
    project_id: str
    asset_type: str
    original_name: str
    file_path: str
    mime_type: str | None
    size_bytes: int
    meta: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


class TaskCreate(BaseModel):
    task_type: str
    params: dict[str, Any] = Field(default_factory=dict)


class AssetDelete(BaseModel):
    asset_ids: list[str] = Field(min_length=1, max_length=1000)


class TaskRead(BaseModel):
    id: str
    project_id: str
    task_type: str
    status: str
    progress: int
    message: str
    rq_job_id: str | None
    params: dict[str, Any]
    result: dict[str, Any]
    error: str | None
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None
    finished_at: datetime | None

    model_config = {"from_attributes": True}


class DatasetFileRead(BaseModel):
    file_name: str
    image_url: str
    label_url: str | None = None
    metadata_url: str | None = None


class DatasetGalleryRead(BaseModel):
    dataset_id: str
    name: str
    created_at: datetime
    label_format: str | None = None
    layout_mode: str | None = None
    total_images: int
    files: list[DatasetFileRead]
