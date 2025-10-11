"""Element detection using Google Gemini."""
from __future__ import annotations

import logging
from typing import Dict, List
import google.generativeai as genai

from ..core.config import settings
from ..services.fdx_parser import ParsedScene, ParsedSceneElement

logger = logging.getLogger(__name__)


ELEMENT_CATEGORIES = [
    "Cast",
    "Extras",
    "Props",
    "Set Dressing",
    "Wardrobe",
    "Makeup & Hair",
    "Vehicles/Animals",
    "Sound FX",
    "Special Effects",
    "Stunts"
]


class ElementDetector:
    """Detect production elements using Google Gemini."""

    def __init__(self):
        if not settings.GOOGLE_API_KEY:
            logger.warning("GOOGLE_API_KEY not configured. Element detection will be disabled.")
            self.model = None
        else:
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            self.model = genai.GenerativeModel(settings.CHAT_MODEL)

    async def detect_elements(self, scenes: List[ParsedScene]) -> Dict[str, List[ParsedSceneElement]]:
        """
        Detect production elements for a list of scenes.

        Returns:
            Dict mapping scene.id to list of SceneElement objects
        """
        if not self.model:
            logger.warning("Gemini model not configured. Skipping element detection.")
            return {}

        elements_map = {}

        for scene in scenes:
            try:
                elements = await self._detect_scene_elements(scene)
                if elements:
                    elements_map[scene.id] = elements
            except Exception as e:
                logger.warning(f"Failed to detect elements for scene {scene.name}: {e}")
                continue

        return elements_map

    async def _detect_scene_elements(self, scene: ParsedScene) -> List[ParsedSceneElement]:
        """Detect elements for a single scene."""
        prompt = f"""Analyze this film scene and identify production elements needed.

Scene: {scene.name}
Slugline: {scene.slugline}
Content: {scene.script_excerpt[:1000] if scene.script_excerpt else ''}

For each element found, categorize it into one of: {', '.join(ELEMENT_CATEGORIES)}

Provide the output as a simple list, one element per line in the format:
CATEGORY: Element Name - Brief description

Example:
Props: Coffee cup - Ceramic mug
Wardrobe: Police uniform - Full LAPD uniform
Vehicles/Animals: Police car - Black and white patrol car

Elements:"""

        response = self.model.generate_content(prompt)
        text = response.text.strip()

        elements = []
        for line in text.split('\n'):
            line = line.strip()
            if not line or ':' not in line:
                continue

            try:
                category_part, rest = line.split(':', 1)
                category = category_part.strip()

                if category not in ELEMENT_CATEGORIES:
                    continue

                # Parse element name and description
                rest = rest.strip()
                if ' - ' in rest:
                    name, description = rest.split(' - ', 1)
                else:
                    name = rest
                    description = None

                element = ParsedSceneElement(
                    category=category,
                    name=name.strip(),
                    description=description.strip() if description else None
                )
                elements.append(element)
            except Exception as e:
                logger.debug(f"Failed to parse element line: {line} - {e}")
                continue

        return elements
