from __future__ import annotations

from collections.abc import Mapping

from ...db.models import SceneModel
from ...schemas.scene import Scene, SceneCastAssignment


AssignmentLookup = Mapping[str, dict[str, object]]


def scene_model_to_schema(
    model: SceneModel,
    assignments: AssignmentLookup | None = None,
) -> Scene:
    cast_details: list[SceneCastAssignment] = []

    for cast in model.cast_members:
        character_name = cast.performer_name or ""
        normalized = character_name.strip().upper()
        assignment = assignments.get(normalized) if assignments else None

        actor_id = assignment.get("actor_id") if assignment else None
        actor_name = assignment.get("actor_name") if assignment else None
        union_status = assignment.get("union_status") if assignment else None

        cast_details.append(
            SceneCastAssignment(
                character_name=character_name,
                actor_id=int(actor_id) if isinstance(actor_id, int) else None,
                actor_name=str(actor_name) if actor_name else None,
                union_status=str(union_status) if union_status else None,
            )
        )

    return Scene(
        id=str(model.id),
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
        cast_details=cast_details,
        props=[prop.prop_name for prop in model.props_used],
        script_day=model.script_day,
        schedule_day_id=str(model.schedule_day_id) if model.schedule_day_id else None,
    )
