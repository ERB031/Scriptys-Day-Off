from __future__ import annotations

from dataclasses import dataclass
from typing import List
from uuid import uuid4

from ..schemas.schedule import DayPlan
from ..schemas.scene import Scene


@dataclass
class SchedulingRule:
    max_pages_per_day: float = 12.0
    max_minutes_per_day: float = 12.0 * 60.0


class AutoScheduler:
    def __init__(self, rule: SchedulingRule | None = None) -> None:
        self.rule = rule or SchedulingRule()

    def build(self, scenes: List[Scene]) -> List[DayPlan]:
        if not scenes:
            return []

        # Sort scenes by user-defined day (if any), location, and sequence to minimize company moves.
        sorted_scenes = sorted(
            scenes,
            key=lambda s: (
                s.script_day if s.script_day is not None else float("inf"),
                s.location,
                s.sequence_index,
            ),
        )

        plans: list[DayPlan] = []
        current_scenes: list[Scene] = []
        current_pages = 0.0
        current_minutes = 0.0
        current_script_day = sorted_scenes[0].script_day if sorted_scenes else None

        for scene in sorted_scenes:
            requested_day = scene.script_day
            script_day_changed = (
                requested_day is not None
                and current_scenes
                and requested_day != current_script_day
            )

            page_candidate = current_pages + scene.page_decimal
            minute_candidate = current_minutes + scene.estimated_minutes

            if (
                script_day_changed
                or page_candidate > self.rule.max_pages_per_day
                or minute_candidate > self.rule.max_minutes_per_day
            ):
                if current_scenes:
                    plans.append(self._build_day_plan(current_scenes))
                current_scenes = []
                current_pages = 0.0
                current_minutes = 0.0
                current_script_day = requested_day

            current_scenes.append(scene)
            current_pages += scene.page_decimal
            current_minutes += scene.estimated_minutes
            if current_script_day is None:
                current_script_day = requested_day

        if current_scenes:
            plans.append(self._build_day_plan(current_scenes))

        if len(plans) > 20:
            raise ValueError("Auto-schedule would exceed the 20 day limit. Adjust scene assignments.")

        # Ensure day names are neatly labeled.
        for idx, plan in enumerate(plans, start=1):
            primary_location = plan.shooting_location or (plan.location_summary[0] if plan.location_summary else "Mixed")
            script_days = sorted({scene.script_day for scene in plan.scenes if scene.script_day is not None})
            if len(script_days) == 1:
                plan.name = f"Day {script_days[0]} - {primary_location}"
            else:
                plan.name = f"Day {idx} - {primary_location}"
            plan.id = plan.id or str(uuid4())

        return plans

    def _build_day_plan(self, scenes: List[Scene]) -> DayPlan:
        total_cost = sum(scene.estimated_cost for scene in scenes)
        total_minutes = sum(scene.estimated_minutes for scene in scenes)
        total_pages = sum(scene.page_decimal for scene in scenes)
        location_summary = sorted({scene.location for scene in scenes})
        cast_summary = sorted({
            cast_detail.actor_name if cast_detail.actor_name else cast_detail.character_name
            for scene in scenes
            for cast_detail in scene.cast_details
        })
        if not cast_summary:
            cast_summary = sorted({cast for scene in scenes for cast in scene.cast})

        shooting_location = location_summary[0] if location_summary else None

        return DayPlan(
            id=str(uuid4()),
            name="",
            shooting_date=None,
            shooting_location=shooting_location,
            total_cost=round(total_cost, 2),
            total_minutes=round(total_minutes, 2),
            total_pages_decimal=round(total_pages, 2),
            location_summary=location_summary,
            cast_summary=cast_summary,
            scenes=scenes,
        )

