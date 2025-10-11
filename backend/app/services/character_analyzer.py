"""Character analysis using Google Gemini."""
from __future__ import annotations

import logging
from typing import Dict, List, Set
import google.generativeai as genai

from ..core.config import settings
from ..services.fdx_parser import ParsedScene

logger = logging.getLogger(__name__)


class CharacterAnalyzer:
    """Analyze characters and cast using Google Gemini."""

    def __init__(self):
        if not settings.GOOGLE_API_KEY:
            logger.warning("GOOGLE_API_KEY not configured. Character analysis will be disabled.")
            self.model = None
        else:
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            self.model = genai.GenerativeModel(settings.CHAT_MODEL)

    async def analyze_characters(self, scenes: List[ParsedScene]) -> Dict[str, Dict]:
        """
        Analyze characters across all scenes.

        Returns:
            Dict mapping character name to analysis data
        """
        if not self.model:
            logger.warning("Gemini model not configured. Skipping character analysis.")
            return {}

        # Collect all unique characters
        all_characters: Set[str] = set()
        for scene in scenes:
            all_characters.update(scene.cast)

        # For now, just return basic info
        # This could be expanded to analyze character importance, relationships, etc.
        character_info = {}
        for character in all_characters:
            scenes_with_char = [s.name for s in scenes if character in s.cast]
            character_info[character] = {
                "name": character,
                "scene_count": len(scenes_with_char),
                "scenes": scenes_with_char
            }

        return character_info

    async def suggest_cast_grouping(self, scenes: List[ParsedScene]) -> List[List[str]]:
        """
        Suggest optimal groupings of scenes based on cast availability.

        Returns:
            List of scene ID groups that share similar cast
        """
        if not self.model:
            logger.warning("Gemini model not configured. Skipping cast grouping.")
            return []

        # This is a placeholder for more sophisticated AI-based grouping
        # For now, just group scenes with identical cast
        cast_groups: Dict[frozenset, List[str]] = {}

        for scene in scenes:
            cast_key = frozenset(scene.cast)
            if cast_key not in cast_groups:
                cast_groups[cast_key] = []
            cast_groups[cast_key].append(scene.id)

        return list(cast_groups.values())
