from __future__ import annotations

from dataclasses import dataclass
from typing import List
from uuid import uuid4

from ..schemas.schedule import DayPlan
from ..schemas.scene import Scene


@dataclass
class SchedulingRule:
    max_pages_per_day: float = 5.0
    max_minutes_per_day: float = 480.0


class AutoScheduler:
    def __init__(self, rule: SchedulingRule | None = None) -> None:
        self.rule = rule or SchedulingRule()

    def build(self, scenes: List[Scene]) -> List[DayPlan]:
        if not scenes:
            return []

        # Sort scenes by location and sequence to minimize company moves.
        sorted_scenes = sorted(
            scenes,
            key=lambda s: (s.location, s.sequence_index),
        )

        plans: list[DayPlan] = []
        current_scenes: list[Scene] = []
        current_pages = 0.0
        current_minutes = 0.0

        for scene in sorted_scenes:
            page_candidate = current_pages + scene.page_decimal
            minute_candidate = current_minutes + scene.estimated_minutes

            if page_candidate > self.rule.max_pages_per_day or minute_candidate > self.rule.max_minutes_per_day:
                if current_scenes:
                    plans.append(self._build_day_plan(current_scenes))
                current_scenes = []
                current_pages = 0.0
                current_minutes = 0.0

            current_scenes.append(scene)
            current_pages += scene.page_decimal
            current_minutes += scene.estimated_minutes

        if current_scenes:
            plans.append(self._build_day_plan(current_scenes))

        # Ensure day names are neatly labeled.
        for idx, plan in enumerate(plans, start=1):
            primary_location = plan.location_summary[0] if plan.location_summary else "Mixed"
            plan.name = f"Day {idx} – {primary_location}"
            plan.id = plan.id or str(uuid4())

        return plans

    def _build_day_plan(self, scenes: List[Scene]) -> DayPlan:
        total_cost = sum(scene.estimated_cost for scene in scenes)
        total_minutes = sum(scene.estimated_minutes for scene in scenes)
        total_pages = sum(scene.page_decimal for scene in scenes)
        location_summary = sorted({scene.location for scene in scenes})
        cast_summary = sorted({cast for scene in scenes for cast in scene.cast})

        return DayPlan(
            id=str(uuid4()),
            name="",
            shooting_date=None,
            total_cost=round(total_cost, 2),
            total_minutes=round(total_minutes, 2),
            total_pages_decimal=round(total_pages, 2),
            location_summary=location_summary,
            cast_summary=cast_summary,
            scenes=scenes,
        )
