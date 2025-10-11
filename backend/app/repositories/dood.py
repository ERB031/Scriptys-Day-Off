from typing import List, Dict, Set
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from ..schemas.dood import DayOutOfDays, CastMemberDays
from .scenes import list_scenes_for_upload

async def get_dood_report(session: AsyncSession, upload_id: UUID) -> DayOutOfDays:
    scenes = await list_scenes_for_upload(session, upload_id)

    cast_members: Set[str] = set()
    for scene in scenes:
        for cast_member in scene.cast_members:
            cast_members.add(cast_member.performer_name)

    shooting_days: Set[int] = set()
    for scene in scenes:
        if scene.script_day is not None:
            shooting_days.add(scene.script_day)

    sorted_shooting_days = sorted(list(shooting_days))

    cast_member_days: List[CastMemberDays] = []
    for cast_member_name in sorted(list(cast_members)):
        days: Dict[int, str] = {}
        work_days = {
            scene.script_day
            for scene in scenes
            if scene.script_day is not None
            and cast_member_name in [cm.performer_name for cm in scene.cast_members]
        }

        if not work_days:
            continue

        first_work_day = min(work_days)
        last_work_day = max(work_days)

        for day in sorted_shooting_days:
            if day in work_days:
                if day == first_work_day:
                    days[day] = 'S'
                elif day == last_work_day:
                    days[day] = 'F'
                else:
                    days[day] = 'W'
            elif first_work_day < day < last_work_day:
                days[day] = 'H'
            else:
                days[day] = 'I'

        cast_member_days.append(
            CastMemberDays(cast_member_name=cast_member_name, days=days)
        )

    return DayOutOfDays(
        shooting_days=sorted_shooting_days,
        cast_members=cast_member_days,
    )
