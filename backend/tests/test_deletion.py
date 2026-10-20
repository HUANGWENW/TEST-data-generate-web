"""Local API/database/filesystem regression tests; never uses the live service."""
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "sqlite://")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.projects import router
from app.core.config import get_settings
from app.core.database import Base, get_db
from app.models.entities import Asset, GenerationTask, Project
from app.services.storage import project_root


@compiles(JSONB, "sqlite")
def sqlite_jsonb(type_, compiler, **kwargs):
    # Production remains PostgreSQL/JSONB; tests exercise ordinary JSON values.
    return "JSON"


class DeletionApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.env = patch.dict(os.environ, {"STORAGE_ROOT": str(self.root / "storage")})
        self.env.start()
        get_settings.cache_clear()
        self.engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})

        @event.listens_for(self.engine, "connect")
        def enable_foreign_keys(connection, record):
            connection.execute("PRAGMA foreign_keys=ON")

        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(self.engine, expire_on_commit=False)
        self.db = self.sessions()
        self.project = self.add_project("待删除的测试项目")
        self.other = self.add_project("保留的测试项目")

        def session_override():
            with self.sessions() as session:
                yield session

        app = FastAPI()
        app.include_router(router, prefix="/api")
        app.dependency_overrides[get_db] = session_override
        app.mount("/storage", StaticFiles(directory=self.root / "storage"))
        self.client = TestClient(app)
        self.base = f"/api/projects/{self.project.id}"

    def tearDown(self):
        self.client.close()
        self.db.close()
        self.engine.dispose()
        self.env.stop()
        get_settings.cache_clear()
        self.temp.cleanup()

    def add_project(self, name):
        project = Project(name=name)
        self.db.add(project)
        self.db.commit()
        project_root(project.id)
        return project

    def add_asset(self, kind="mask", project=None, path=None, meta=None):
        project = project or self.project
        directory = project_root(project.id) / {"mask": "masks", "part": "parts", "dataset": "synthetic"}.get(kind, "uploads")
        path = path or directory / f"file_{len(self.db.scalars(select(Asset)).all())}.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_bytes(b"test-file-content")
        asset = Asset(project_id=project.id, asset_type=kind, original_name=path.name, file_path=str(path), size_bytes=path.stat().st_size, meta={"width": 40, "height": 20, **(meta or {})})
        self.db.add(asset)
        self.db.commit()
        return asset

    def add_task(self, status="succeeded", project=None):
        task = GenerationTask(project_id=(project or self.project).id, task_type="masks_to_parts", status=status, progress=100, params={})
        self.db.add(task)
        self.db.commit()
        return task

    def delete_assets(self, *ids):
        return self.client.post(self.base + "/assets/delete", json={"asset_ids": list(ids)})

    def exists(self, model, id_):
        with self.sessions() as session:
            return session.get(model, id_) is not None

    def test_project_deletes_own_records_and_files_only(self):
        mask = self.add_asset()
        task = self.add_task()
        other_asset = self.add_asset(project=self.other)
        response = self.client.delete(self.base)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")
        self.assertFalse(self.exists(Project, self.project.id))
        self.assertFalse(self.exists(Asset, mask.id))
        self.assertFalse(self.exists(GenerationTask, task.id))
        self.assertFalse((self.root / "storage/projects" / self.project.id).exists())
        self.assertTrue(self.exists(Project, self.other.id))
        self.assertTrue(Path(other_asset.file_path).exists())
        self.assertEqual(self.client.get(self.base).status_code, 404)

    def test_deleted_project_disappears_from_list(self):
        self.client.delete(self.base)
        listed = self.client.get("/api/projects").json()
        self.assertEqual([item["id"] for item in listed], [self.other.id])
        self.assertEqual(self.client.delete(self.base).status_code, 404)

    def test_mask_deletion_keeps_generated_part_and_history(self):
        mask = self.add_asset()
        part = self.add_asset("part", meta={"source_asset_id": mask.id})
        task = self.add_task()
        response = self.delete_assets(mask.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["deleted_ids"], [mask.id])
        self.assertFalse(Path(mask.file_path).exists())
        self.assertFalse(self.exists(Asset, mask.id))
        self.assertTrue(Path(part.file_path).exists())
        self.assertTrue(self.exists(GenerationTask, task.id))
        self.assertEqual([a["id"] for a in self.client.get(self.base + "/assets").json()], [part.id])

    def test_part_deletion_keeps_dataset(self):
        part = self.add_asset("part")
        dataset = self.add_asset("dataset")
        response = self.client.delete(self.base + "/assets/" + part.id)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Path(part.file_path).exists())
        self.assertTrue(Path(dataset.file_path).exists())
        self.assertTrue(self.exists(Asset, dataset.id))

    def test_bulk_deletion_deduplicates_and_preserves_unselected(self):
        first = self.add_asset()
        second = self.add_asset()
        keep = self.add_asset()
        response = self.delete_assets(first.id, second.id, first.id)
        self.assertEqual(response.json()["deleted_ids"], [first.id, second.id])
        self.assertFalse(Path(first.file_path).exists())
        self.assertFalse(Path(second.file_path).exists())
        self.assertTrue(Path(keep.file_path).exists())

    def test_cross_project_batch_fails_without_partial_deletion(self):
        own = self.add_asset()
        other = self.add_asset(project=self.other)
        response = self.delete_assets(own.id, other.id)
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Path(own.file_path).exists())
        self.assertTrue(Path(other.file_path).exists())
        self.assertTrue(self.exists(Asset, own.id))

    def test_missing_asset_batch_fails_without_partial_deletion(self):
        own = self.add_asset()
        self.assertEqual(self.delete_assets(own.id, "missing").status_code, 404)
        self.assertTrue(Path(own.file_path).exists())

    def test_other_asset_types_cannot_be_deleted_in_review(self):
        own = self.add_asset()
        source = self.add_asset("input")
        self.assertEqual(self.delete_assets(own.id, source.id).status_code, 422)
        self.assertTrue(Path(own.file_path).exists())
        self.assertTrue(Path(source.file_path).exists())

    def test_active_project_blocks_both_deletion_endpoints(self):
        for status in ("queued", "running"):
            with self.subTest(status=status):
                task = self.add_task(status)
                mask = self.add_asset()
                self.assertEqual(self.client.delete(self.base).status_code, 409)
                self.assertEqual(self.delete_assets(mask.id).status_code, 409)
                self.assertTrue(Path(mask.file_path).exists())
                task.status = "succeeded"
                self.db.commit()

    def test_other_project_active_task_does_not_block(self):
        self.add_task("running", project=self.other)
        self.assertEqual(self.client.delete(self.base).status_code, 204)

    def test_missing_file_record_can_still_be_deleted(self):
        mask = self.add_asset()
        Path(mask.file_path).unlink()
        self.assertEqual(self.delete_assets(mask.id).status_code, 200)
        self.assertFalse(self.exists(Asset, mask.id))

    def test_shared_file_remains_until_last_asset_is_deleted(self):
        first = self.add_asset()
        second = self.add_asset(path=Path(first.file_path))
        self.assertEqual(self.delete_assets(first.id).status_code, 200)
        self.assertTrue(Path(second.file_path).exists())
        self.assertEqual(self.delete_assets(second.id).status_code, 200)
        self.assertFalse(Path(second.file_path).exists())

    def test_path_outside_project_is_rejected(self):
        outside = self.add_asset(path=self.root / "unrelated.png")
        self.assertEqual(self.delete_assets(outside.id).status_code, 409)
        self.assertTrue(Path(outside.file_path).exists())
        self.assertTrue(self.exists(Asset, outside.id))

    def test_database_failure_restores_files_and_records(self):
        mask = self.add_asset()
        with patch("sqlalchemy.orm.Session.commit", side_effect=SQLAlchemyError("test database failure")):
            response = self.delete_assets(mask.id)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(Path(mask.file_path).read_bytes(), b"test-file-content")
        self.assertTrue(self.exists(Asset, mask.id))

    def test_project_database_failure_restores_directory(self):
        mask = self.add_asset()
        with patch("sqlalchemy.orm.Session.commit", side_effect=SQLAlchemyError("test database failure")):
            response = self.client.delete(self.base)
        self.assertEqual(response.status_code, 500)
        self.assertTrue(Path(mask.file_path).exists())
        self.assertTrue(self.exists(Project, self.project.id))

    def test_file_failure_rolls_back_previously_staged_files(self):
        first, second = self.add_asset(), self.add_asset()
        original_rename = Path.rename

        def fail_on_second(path, target):
            if path == Path(second.file_path):
                raise PermissionError("test locked file")
            return original_rename(path, target)

        with patch.object(Path, "rename", fail_on_second):
            response = self.delete_assets(first.id, second.id)
        self.assertEqual(response.status_code, 500)
        self.assertTrue(Path(first.file_path).exists())
        self.assertTrue(Path(second.file_path).exists())
        self.assertTrue(self.exists(Asset, first.id))

    def test_stale_selection_is_rejected_before_enqueue(self):
        mask = self.add_asset()
        self.delete_assets(mask.id)
        with patch("app.api.projects.Queue") as queue:
            response = self.client.post(self.base + "/tasks", json={"task_type": "masks_to_parts", "params": {"mask_asset_ids": [mask.id]}})
        self.assertEqual(response.status_code, 409)
        queue.assert_not_called()
        with self.sessions() as session:
            self.assertEqual(session.scalars(select(GenerationTask)).all(), [])

    def test_validation_rejects_empty_bulk_request(self):
        self.assertEqual(self.delete_assets().status_code, 422)

    def test_upload_and_task_creation_reject_deleted_project(self):
        self.client.delete(self.base)
        self.assertEqual(self.client.post(self.base + "/tasks", json={"task_type": "extract_edge_masks", "params": {}}).status_code, 404)
        response = self.client.post(self.base + "/assets/upload?asset_type=mask", files={"file": ("test.png", b"test", "image/png")})
        self.assertEqual(response.status_code, 404)
        self.assertFalse((self.root / "storage/projects" / self.project.id).exists())


if __name__ == "__main__":
    unittest.main()
