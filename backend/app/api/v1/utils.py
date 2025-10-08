from __future__ import annotations

from ...db.models import SceneModel
from ...schemas.scene import Scene


def scene_model_to_schema(model: SceneModel) -> Scene:
    return Scene(
        id=model.id,
        name=model.name,
        sequence_index=model.sequence_index,
        slugline=model.slugline,
        page_eighths=model.page_eighths,
        page_decimal=model.page_decimal,
        estimated_minutes=model.estimated_minutes,
        location=model.location,
        day_night=model.day_night,
        estimated_cost=model.estimated_cost,
        cast=[cast.performer_name for cast in model.cast_members],
        props=[prop.prop_name for prop in model.props_used],
        script_day=None,
        schedule_day_id=model.schedule_day_id,
    )
