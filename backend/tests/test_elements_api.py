from __future__ import annotations

import asyncio
from datetime import datetime
from uuid import uuid4

import pytest
import sys
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.db.models import (
    ElementCategoryModel,
    SceneCastModel,
    SceneElementModel,
    SceneModel,
    SceneNoteModel,
    ScenePropModel,
    SceneTagModel,
    ScriptUploadModel,
)
from app.db.session import AsyncSessionMaker
from app.main import app

pytestmark = pytest.mark.skipif(
    sys.platform.startswith("win"),
    reason="asyncpg integration tests are unreliable on Windows event loop",
)
@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def sample_scene():
    upload_id = uuid4()
    scene_id = uuid4()

    async def _create() -> dict[str, object]:
        async with AsyncSessionMaker() as session:
            categories = (
                await session.execute(select(ElementCategoryModel))
            ).scalars().all()
            category_lookup = {category.category_name: category for category in categories}

            upload = ScriptUploadModel(
                id=upload_id,
                original_filename="test.fdx",
                mime_type="application/vnd.finaldraft.fdx",
                uploaded_at=datetime.utcnow(),
                total_scenes=1,
                total_pages_decimal=1.0,
                status="parsed",
            )

            scene = SceneModel(
                id=scene_id,
                upload_id=upload_id,
                name="Scene 1",
                sequence_index=1,
                slugline="INT. OFFICE - DAY",
                page_eighths=8,
                page_decimal=1.0,
                estimated_minutes=1.5,
                location="Office",
                day_night="DAY",
                estimated_cost=1500.0,
                synopsis="A tense meeting in the office.",
            )

            scene.cast_members.append(SceneCastModel(performer_name="JANE"))
            scene.props_used.append(ScenePropModel(prop_name="Laptop"))
            scene.tags.append(SceneTagModel(tag="INT"))
            scene.notes.append(SceneNoteModel(note_text="Use dolly shot", note_type="CAMERA"))

            cast_category = category_lookup.get("Cast")
            props_category = category_lookup.get("Props")
            if cast_category:
                scene.elements.append(
                    SceneElementModel(
                        category_id=cast_category.id,
                        category=cast_category,
                        element_name="JANE",
                        quantity=1,
                        description="Lead actor",
                        is_critical=True,
                    )
                )
            if props_category:
                scene.elements.append(
                    SceneElementModel(
                        category_id=props_category.id,
                        category=props_category,
                        element_name="Laptop",
                        quantity=1,
                    )
                )

            session.add_all([upload, scene])
            await session.commit()

        return {
            "upload_id": str(upload_id),
            "scene_id": str(scene_id),
            "category_ids": {name: category.id for name, category in category_lookup.items()},
        }

    data = asyncio.run(_create())

    yield data

    async def _cleanup():
        async with AsyncSessionMaker() as session:
            await session.execute(delete(ScriptUploadModel).where(ScriptUploadModel.id == upload_id))
            await session.commit()

    asyncio.run(_cleanup())


def test_get_scene_elements(client: TestClient, sample_scene):
    response = client.get(f"/api/v1/elements/scenes/{sample_scene['scene_id']}/elements")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    category_names = {item["category_name"] for item in data}
    assert "Cast" in category_names
    assert all(item["category_color"] for item in data if item["category_name"])


def test_breakdown_sheet_for_scene(client: TestClient, sample_scene):
    response = client.get(f"/api/v1/breakdown/scenes/{sample_scene['scene_id']}/breakdown")
    assert response.status_code == 200
    sheet = response.json()
    assert sheet["scene_id"] == sample_scene["scene_id"]
    assert sheet["slugline"] == "INT. OFFICE - DAY"
    assert sheet["int_ext"] == "INT"
    assert any(el["element_name"] == "Laptop" for el in sheet["props"])
    assert sheet["camera_notes"] == ["Use dolly shot"]


def test_master_elements_endpoint(client: TestClient, sample_scene):
    response = client.get(
        f"/api/v1/elements/uploads/{sample_scene['upload_id']}/master-elements"
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(item["category_name"] == "Props" for item in data)


def test_create_update_delete_scene_element(client: TestClient, sample_scene):
    category_id = sample_scene["category_ids"].get("Special Effects")
    if not category_id:
        pytest.skip("Special Effects category not available in test database.")

    payload = {
        "scene_id": sample_scene["scene_id"],
        "category_id": category_id,
        "element_name": "Spark Shower",
        "quantity": 1,
        "is_critical": True,
    }

    create_resp = client.post(
        f"/api/v1/elements/scenes/{sample_scene['scene_id']}/elements",
        json=payload,
    )
    assert create_resp.status_code == 201
    created_element = create_resp.json()
    assert created_element["category_name"] == "Special Effects"

    element_id = created_element["id"]

    update_resp = client.patch(
        f"/api/v1/elements/scenes/{sample_scene['scene_id']}/elements/{element_id}",
        json={"quantity": 3},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["quantity"] == 3

    delete_resp = client.delete(
        f"/api/v1/elements/scenes/{sample_scene['scene_id']}/elements/{element_id}"
    )
    assert delete_resp.status_code == 204

    list_resp = client.get(f"/api/v1/elements/scenes/{sample_scene['scene_id']}/elements")
    assert list_resp.status_code == 200
    ids = {item["id"] for item in list_resp.json()}
    assert element_id not in ids
