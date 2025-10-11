from sqlalchemy.ext.asyncio import AsyncSession
from ..db.models import SceneElementModel
from ..schemas.elements import SceneElementCreate

async def create_scene_element(session: AsyncSession, element: SceneElementCreate) -> SceneElementModel:
    db_element = SceneElementModel(**element.model_dump())
    session.add(db_element)
    await session.commit()
    await session.refresh(db_element)
    return db_element
