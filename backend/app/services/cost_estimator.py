from __future__ import annotations

from typing import List

from openai import AsyncOpenAI

from ..core.config import settings
from ..schemas.scene import Scene


class CostEstimator:
    def __init__(self) -> None:
        if settings.openai_api_key:
            self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        else:
            self.client = None

    async def estimate_scene_costs(self, scenes: List[Scene]) -> List[float]:
        if not self.client:
            # Without an API key we default estimates to zero.
            return [0.0 for _ in scenes]

        prompt = self._build_prompt(scenes)
        response = await self.client.responses.create(
            model=settings.chat_model,
            input=prompt,
        )

        # TODO: parse response into floats.
        raise NotImplementedError("Cost estimation parsing still pending.")

    def _build_prompt(self, scenes: List[Scene]) -> str:
        lines = [
            "You are an experienced line producer generating rough cost estimates per scene.",
            "Return JSON with scene_id and estimated_cost fields."
        ]
        for scene in scenes:
            lines.append(
                f"Scene {scene.id}: slugline={scene.slugline}, length={scene.page_decimal} pages, cast={scene.cast}, props={scene.props}"
            )
        return "\n".join(lines)

