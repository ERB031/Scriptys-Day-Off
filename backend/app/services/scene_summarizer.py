"""Scene synopsis generation using Google Gemini."""
from __future__ import annotations

import logging
from typing import Dict, List
import google.generativeai as genai

from ..core.config import settings
from ..services.fdx_parser import ParsedScene

logger = logging.getLogger(__name__)


class SceneSummarizer:
    """Generate scene synopses using Google Gemini."""

    def __init__(self):
        if not settings.GOOGLE_API_KEY:
            logger.warning("GOOGLE_API_KEY not configured. Scene synopsis generation will be disabled.")
            self.model = None
        else:
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            self.model = genai.GenerativeModel(settings.CHAT_MODEL)

    async def generate_synopses(self, scenes: List[ParsedScene]) -> Dict[str, str]:
        """
        Generate synopses for a list of scenes.

        Returns:
            Dict mapping scene.id to synopsis text
        """
        if not self.model:
            logger.warning("Gemini model not configured. Skipping synopsis generation.")
            return {}

        synopsis_map = {}

        for scene in scenes:
            try:
                synopsis = await self._generate_single_synopsis(scene)
                if synopsis:
                    synopsis_map[scene.id] = synopsis
            except Exception as e:
                logger.warning(f"Failed to generate synopsis for scene {scene.name}: {e}")
                continue

        return synopsis_map

    async def _generate_single_synopsis(self, scene: ParsedScene) -> str:
        """Generate synopsis for a single scene."""
        prompt = f"""Generate a professional, concise 1-2 sentence synopsis for this film scene.
Focus on the dramatic beats and key characters.

Scene: {scene.name}
Slugline: {scene.slugline}
Page Length: {scene.page_decimal:.2f} pages
Content: {scene.script_excerpt[:500] if scene.script_excerpt else ''}

Synopsis:"""

        response = self.model.generate_content(prompt)
        synopsis = response.text.strip()

        # Clean up the synopsis
        if synopsis.startswith('"') and synopsis.endswith('"'):
            synopsis = synopsis[1:-1]

        return synopsis
