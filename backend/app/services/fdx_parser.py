from __future__ import annotations

import math
import re
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from io import BytesIO
from typing import Dict, Iterable, List, Optional, Tuple
from uuid import uuid4


@dataclass
class ParsedSceneElement:
    category: str
    name: str
    quantity: int = 1
    description: Optional[str] = None
    is_critical: bool = False


@dataclass
class ParsedScene:
    id: str
    name: str
    sequence_index: int
    slugline: str
    page_eighths: int
    page_decimal: float
    estimated_minutes: float
    location: str
    day_night: str
    cast: List[str]
    props: List[str]
    estimated_cost: float = 0.0
    elements: List[ParsedSceneElement] = field(default_factory=list)
    script_excerpt: str = ""
    synopsis: Optional[str] = None


class FDXParser:
    """Parse Final Draft FDX files into structured scene metadata."""

    UPPERCASE_PHRASE_PATTERN = re.compile(
        r"\b([A-Z][A-Z0-9'&\-]*(?:\s+[A-Z][A-Z0-9'&\-]*){0,3})\b"
    )
    ELEMENT_STOPWORDS = {
        "THE",
        "AND",
        "OR",
        "OF",
        "A",
        "AN",
        "IN",
        "ON",
        "TO",
        "BY",
        "WITH",
        "AT",
        "FOR",
        "FROM",
        "UP",
        "DOWN",
        "OUT",
        "BACK",
        "CUT",
        "FADE",
        "ANGLE",
        "SHOT",
        "CONTINUOUS",
        "MOMENTS",
        "LATER",
        "SAME",
        "TIME",
        "MEANWHILE",
        "HE",
        "SHE",
        "THEY",
        "WE",
        "YOU",
        "I",
        "IT",
        "ITS",
        "INT",
        "EXT",
        "INT/EXT",
        "DAY",
        "NIGHT",
        "EVENING",
        "MORNING",
        "AFTERNOON",
        "NOON",
        "MIDNIGHT",
        "BEAT",
        "BEATS",
        "V.O.",
        "O.S.",
        "CONT'D",
    }
    EXTRAS_KEYWORDS = {
        "CROWD",
        "PEOPLE",
        "PASSERSBY",
        "PASSERS-BY",
        "PEDESTRIANS",
        "CUSTOMERS",
        "STUDENTS",
        "CLASSMATES",
        "WAITERS",
        "WAITRESSES",
        "DINERS",
        "GUESTS",
        "SPECTATORS",
        "AUDIENCE",
        "PATIENTS",
        "NURSES",
        "DOCTORS",
        "OFFICERS",
        "GUARDS",
        "SOLDIERS",
        "COPS",
        "FIREFIGHTERS",
        "REPORTERS",
        "PAPARAZZI",
        "STAFF",
        "WORKERS",
    }
    VEHICLE_KEYWORDS = {
        "CAR",
        "CARS",
        "TRUCK",
        "TRUCKS",
        "SUV",
        "SUVS",
        "VAN",
        "VANS",
        "BUS",
        "BUSES",
        "MOTORCYCLE",
        "MOTORCYCLES",
        "BIKE",
        "BIKES",
        "BICYCLE",
        "BICYCLES",
        "HELICOPTER",
        "HELICOPTERS",
        "PLANE",
        "PLANES",
        "JET",
        "JETS",
        "BOAT",
        "BOATS",
        "SHIP",
        "SHIPS",
        "TAXI",
        "TAXIS",
        "CAB",
        "CABS",
        "AMBULANCE",
        "AMBULANCES",
        "POLICE CAR",
        "SQUAD CAR",
    }
    ANIMAL_KEYWORDS = {
        "DOG",
        "DOGS",
        "CAT",
        "CATS",
        "HORSE",
        "HORSES",
        "BIRD",
        "BIRDS",
        "RAT",
        "RATS",
        "MOUSE",
        "MICE",
        "COW",
        "COWS",
        "SNAKE",
        "SNAKES",
        "FISH",
        "PIG",
        "PIGS",
    }
    SOUND_KEYWORDS = {
        "SIREN",
        "SIRENS",
        "ALARM",
        "ALARMS",
        "MUSIC",
        "THEME",
        "SCORE",
        "SONG",
        "SONGS",
        "GUNSHOT",
        "GUNSHOTS",
        "GUNFIRE",
        "SHOTS",
        "EXPLOSION",
        "EXPLOSIONS",
        "RINGTONE",
        "PHONE RING",
        "SCREAM",
        "SCREAMS",
    }
    SPECIAL_EFFECTS_KEYWORDS = {
        "EXPLOSION",
        "EXPLOSIONS",
        "FIRE",
        "FLAMES",
        "SMOKE",
        "SPARKS",
        "RAIN",
        "STORM",
        "LIGHTNING",
        "WIND",
        "FOG",
        "BLOOD SPRAY",
        "DEBRIS",
        "SHATTERED GLASS",
    }
    STUNT_KEYWORDS = {
        "FIGHT",
        "FIGHTS",
        "CHASE",
        "CHASES",
        "JUMP",
        "JUMPS",
        "FALL",
        "FALLS",
        "CRASH",
        "CRASHES",
        "COLLISION",
        "COLLISIONS",
        "DIVE",
        "DIVES",
        "PUNCH",
        "PUNCHES",
        "KICK",
        "KICKS",
        "TACKLE",
        "TACKLES",
        "CLIMB",
        "CLIMBS",
    }
    WARDROBE_KEYWORDS = {
        "DRESS",
        "DRESSES",
        "SUIT",
        "SUITS",
        "UNIFORM",
        "UNIFORMS",
        "COAT",
        "COATS",
        "JACKET",
        "JACKETS",
        "HAT",
        "HATS",
        "MASK",
        "MASKS",
        "GLOVES",
        "CLOAK",
        "CLOAKS",
        "CAPE",
        "CAPES",
        "BOOTS",
        "SHOES",
        "HELMET",
        "HELMETS",
    }
    MAKEUP_KEYWORDS = {
        "BLOOD",
        "BRUISE",
        "BRUISES",
        "SCAR",
        "SCARS",
        "MAKEUP",
        "WIG",
        "WIGS",
        "PROSTHETIC",
        "PROSTHETICS",
        "FACE PAINT",
    }
    SET_DRESSING_KEYWORDS = {
        "TABLE",
        "TABLES",
        "CHAIR",
        "CHAIRS",
        "DESK",
        "DESKS",
        "SOFA",
        "COUCH",
        "BED",
        "BEDS",
        "LAMP",
        "LAMPS",
        "PAINTING",
        "PAINTINGS",
        "PICTURE",
        "PICTURES",
        "DECOR",
        "FURNITURE",
        "CABINET",
        "CABINETS",
        "SHELF",
        "SHELVES",
        "BOOKCASE",
        "BOOKSHELF",
        "CARPET",
        "RUG",
        "RUGS",
        "PLANT",
        "PLANTS",
    }
    PROP_KEYWORDS = {
        "GUN",
        "KNIFE",
        "SWORD",
        "PHONE",
        "CELLPHONE",
        "LAPTOP",
        "COMPUTER",
        "BOOK",
        "BOOKS",
        "KEY",
        "KEYS",
        "WALLET",
        "PURSE",
        "BAG",
        "BACKPACK",
        "BRIEFCASE",
        "GLASS",
        "CUP",
        "MUG",
        "BOTTLE",
        "PEN",
        "PENCIL",
        "NOTEBOOK",
        "DOCUMENT",
        "LETTER",
        "ENVELOPE",
        "CIGARETTE",
        "LIGHTER",
        "REMOTE",
        "REMOTE CONTROL",
        "FLASHLIGHT",
        "CAMERA",
        "PHOTO",
        "PHOTOGRAPH",
    }
    ACRONYM_WHITELIST = {
        "FBI",
        "CIA",
        "SWAT",
        "TV",
        "PA",
        "DJ",
        "SUV",
        "NBA",
        "NFL",
        "NYPD",
        "LAPD",
        "DEA",
        "ATF",
    }

    # Calibration multiplier to adjust estimation to match Final Draft
    # Calibrated to match actual FDX page counts
    PAGE_ESTIMATION_MULTIPLIER = 1.044

    def parse(self, file_bytes: bytes) -> List[ParsedScene]:
        import logging
        logger = logging.getLogger(__name__)

        root = self._load_xml(file_bytes)
        logger.info(f"XML root tag: {root.tag}")

        character_lookup = self._build_character_lookup(root)
        logger.info(f"Found {len(character_lookup)} characters in lookup")

        scene_meta = self._extract_scene_meta(root, character_lookup)
        logger.info(f"Found {len(scene_meta)} scenes in metadata")

        paragraphs, scene_order = self._collect_paragraphs(root)
        # Create a set of all known character names for efficient lookup
        all_known_characters = {
            self.normalize_character_name(name) for name in character_lookup.values()
        }
        logger.info(f"Found {len(scene_order)} scenes with {sum(len(p) for p in paragraphs.values())} total paragraphs")

        parsed_scenes: list[ParsedScene] = []
        seen_ids: set[str] = set()

        for scene_id in scene_order:
            meta = scene_meta.get(scene_id, {})
            scene_paragraphs = paragraphs.get(scene_id, [])
            slugline = meta.get("title") or self.first_slugline(scene_paragraphs)
            if not slugline:
                # Skip anything that does not look like a proper SCENE HEADING.
                logger.warning(f"Skipping scene {scene_id}: no slugline found")
                continue

            clean_slugline = self.clean_text(slugline)
            location, day_night = self.parse_location_and_time(clean_slugline)

            # Extract and normalize character names from dialogue
            cast_from_dialogue = self.extract_characters(scene_paragraphs)
            meta_characters = meta.get("characters") or []
            cast_set = set(cast_from_dialogue)
            if meta_characters:
                for character in meta_characters:
                    normalized = self.clean_text(character).upper()
                    if normalized:
                        cast_set.add(normalized)

            # Scan action lines for any other known characters present in the scene
            mentioned_characters = self.find_characters_in_action(scene_paragraphs, all_known_characters)
            cast_set.update(mentioned_characters)
            cast = sorted(cast_set)

            detected_elements = self.detect_scene_elements(scene_paragraphs, cast)
            props = [
                element.name
                for element in detected_elements
                if element.category == "Props"
            ]

            script_lines: list[str] = []
            for paragraph in scene_paragraphs:
                para_type = paragraph.get("type", "")
                text_value = paragraph.get("text", "")
                if not text_value or para_type == "SCENE HEADING":
                    continue
                cleaned_line = self.clean_text(text_value)
                if cleaned_line:
                    script_lines.append(cleaned_line)
            script_excerpt = "\n".join(script_lines)
            if len(script_excerpt) > 2000:
                script_excerpt = script_excerpt[:1997].rstrip() + "..."

            # Get scene length from metadata if available, otherwise estimate from content
            # Priority: 1) Actual page numbers, 2) Metadata, 3) Estimation
            page_eighths = None

            # Try to calculate from actual page numbers first
            actual_eighths = self.calculate_eighths_from_pages(scene_paragraphs)
            if actual_eighths is not None:
                page_eighths = actual_eighths
            # Fall back to metadata
            elif meta.get("length_eighths"):
                page_eighths = meta["length_eighths"]
            # Last resort: estimate from content
            else:
                page_eighths = self.estimate_eighths(scene_paragraphs)

            page_decimal = round(page_eighths / 8.0, 3)
            estimated_minutes = round(page_decimal * 1.0, 2)

            scene_uuid = meta.get("id") or scene_id or str(uuid4())
            if scene_uuid in seen_ids:
                scene_uuid = str(uuid4())
            seen_ids.add(scene_uuid)

            scene_number = meta.get("number") or str(len(parsed_scenes) + 1)
            name = f"Scene {scene_number}"

            parsed_scenes.append(
                ParsedScene(
                    id=scene_uuid,
                    name=name,
                    sequence_index=len(parsed_scenes),
                    slugline=clean_slugline,
                    page_eighths=page_eighths,
                    page_decimal=page_decimal,
                    estimated_minutes=estimated_minutes,
                    location=location,
                    day_night=day_night,
                    cast=cast,
                    props=props,
                    elements=detected_elements,
                    script_excerpt=script_excerpt,
                )
            )

        logger.info(f"Successfully parsed {len(parsed_scenes)} scenes")
        return parsed_scenes

    def _load_xml(self, file_bytes: bytes) -> ET.Element:
        try:
            with zipfile.ZipFile(BytesIO(file_bytes)) as zf:
                xml_name = next(
                    (name for name in zf.namelist() if name.lower().endswith(".xml")),
                    None,
                )
                if not xml_name:
                    raise ValueError("FDX archive missing XML payload.")
                with zf.open(xml_name) as xml_file:
                    data = xml_file.read()
        except zipfile.BadZipFile:
            data = file_bytes

        try:
            return ET.fromstring(data)
        except ET.ParseError as exc:
            raise ValueError("Unable to parse FDX XML") from exc

    def _extract_scene_meta(self, root: ET.Element, character_lookup: Dict[str, str]) -> Dict[str, Dict[str, str | int]]:
        meta: dict[str, dict[str, str | int]] = {}
        for scene in root.findall(".//SceneProperties/Scene"):
            scene_id = scene.attrib.get("SceneID") or scene.attrib.get("ID")
            if not scene_id:
                continue
            length_eighths = self._parse_length(scene)
            characters = self._extract_meta_characters(scene, character_lookup)
            meta[scene_id] = {
                "id": scene_id,
                "number": scene.attrib.get("Number") or scene.attrib.get("SceneNumber"),
                "title": scene.attrib.get("Title"),
                "length_eighths": length_eighths,
                "characters": characters,
            }
        return meta

    def _collect_paragraphs(
        self, root: ET.Element
    ) -> Tuple[Dict[str, list[dict[str, str]]], List[str]]:
        paragraphs: dict[str, list[dict[str, str]]] = {}
        scene_order: list[str] = []

        current_scene_id: str | None = None

        for para in root.findall(".//Content/Paragraph"):
            scene_id = para.attrib.get("SceneID")
            para_type_raw = para.attrib.get("Type", "")
            para_type = self._normalize_para_type(para_type_raw)
            text = "".join(para.itertext())
            text = self.clean_text(text)

            # Extract page number if available
            page_number = para.attrib.get("Page")
            starts_new_page = para.attrib.get("StartsNewPage")

            if not scene_id:
                if para_type == "SCENE HEADING":
                    scene_id = str(uuid4())
                elif current_scene_id:
                    scene_id = current_scene_id
                else:
                    continue

            current_scene_id = scene_id

            if scene_id not in paragraphs:
                paragraphs[scene_id] = []
                scene_order.append(scene_id)

            para_data = {"type": para_type, "text": text}
            if page_number:
                para_data["page_number"] = page_number
            if starts_new_page:
                para_data["starts_new_page"] = starts_new_page

            paragraphs[scene_id].append(para_data)

        return paragraphs, scene_order

    def extract_characters(self, paragraphs: list[dict[str, str]]) -> List[str]:
        """
        Extract and normalize character names from scene paragraphs.

        Handles common screenplay conventions:
        - Removes parentheticals: "ALICE (V.O.)" -> "ALICE"
        - Removes extensions: "BOB (CONT'D)" -> "BOB"
        - Normalizes spacing and capitalization
        - Deduplicates characters
        """
        characters: set[str] = set()

        for paragraph in paragraphs:
            if paragraph["type"] != "CHARACTER":
                continue

            raw_name = self.clean_text(paragraph["text"])
            if not raw_name:
                continue

            normalized = self.normalize_character_name(raw_name)
            if normalized:
                characters.add(normalized)

        return sorted(characters)

    def find_characters_in_action(
        self,
        paragraphs: list[dict[str, str]],
        all_known_characters: set[str]
    ) -> set[str]:
        """
        Find mentions of known characters within action paragraphs.
        This captures characters who are present but do not speak.
        """
        mentioned_characters: set[str] = set()
        scene_text = ""
        for paragraph in paragraphs:
            if paragraph.get("type") == "ACTION":
                scene_text += paragraph.get("text", "") + " "

        if not scene_text:
            return mentioned_characters

        # Check for each known character if they are mentioned as a whole word
        for character_name in all_known_characters:
            if re.search(r'\b' + re.escape(character_name) + r'\b', scene_text, re.IGNORECASE):
                mentioned_characters.add(character_name)
        return mentioned_characters

    def detect_scene_elements(
        self,
        paragraphs: list[dict[str, str]],
        cast: List[str],
    ) -> List[ParsedSceneElement]:
        """
        Heuristically detect production elements (props, vehicles, effects, etc.)
        by scanning action paragraphs for emphatic uppercase phrases.
        """
        cast_tokens = {self.clean_text(name).upper() for name in cast}
        candidates = self._extract_candidate_phrases(paragraphs)
        elements: list[ParsedSceneElement] = []
        seen: set[tuple[str, str]] = set()

        for phrase, prefix in candidates:
            normalized = phrase.strip()
            if not normalized:
                continue
            if normalized in cast_tokens:
                continue
            if normalized in self.ELEMENT_STOPWORDS:
                continue
            if normalized.isdigit():
                continue

            category = self._infer_category(normalized)
            formatted_name = self._format_element_name(normalized)
            key = (category, formatted_name)
            if key in seen:
                continue

            quantity = self._infer_quantity(prefix)
            elements.append(
                ParsedSceneElement(
                    category=category,
                    name=formatted_name,
                    quantity=quantity,
                )
            )
            seen.add(key)
            if len(elements) >= 40:
                break

        return elements

    def _extract_candidate_phrases(
        self,
        paragraphs: list[dict[str, str]],
    ) -> List[tuple[str, str]]:
        candidates: list[tuple[str, str]] = []
        for paragraph in paragraphs:
            if paragraph.get("type") != "ACTION":
                continue
            text = paragraph.get("text") or ""
            if not text:
                continue
            uppercase_text = text.upper()
            for match in self.UPPERCASE_PHRASE_PATTERN.finditer(uppercase_text):
                phrase = match.group(1).strip()
                if not phrase or len(phrase) < 3:
                    continue
                if phrase.count(" ") > 4:
                    continue
                if phrase in self.ELEMENT_STOPWORDS:
                    continue

                prefix = uppercase_text[max(0, match.start() - 8): match.start()]
                candidates.append((phrase, prefix))
        return candidates

    def _infer_category(self, phrase: str) -> str:
        tokens = set(re.split(r"[\s\-]+", phrase))
        if tokens & self.SOUND_KEYWORDS:
            return "Sound FX/Music"
        if tokens & self.SPECIAL_EFFECTS_KEYWORDS:
            return "Special Effects"
        if tokens & self.STUNT_KEYWORDS:
            return "Stunts"
        if (tokens & self.VEHICLE_KEYWORDS) or (tokens & self.ANIMAL_KEYWORDS):
            return "Vehicles/Animals"
        if tokens & self.MAKEUP_KEYWORDS:
            return "Makeup & Hair"
        if tokens & self.WARDROBE_KEYWORDS:
            return "Wardrobe"
        if tokens & self.PROP_KEYWORDS:
            return "Props"
        if tokens & self.SET_DRESSING_KEYWORDS:
            return "Set Dressing"
        if tokens & self.EXTRAS_KEYWORDS or phrase.endswith("EXTRAS"):
            return "Extras"
        return "Set Dressing"  # Default to Set Dressing if not a specific prop

    def _format_element_name(self, phrase: str) -> str:
        def normalize_token(token: str) -> str:
            token_clean = token.strip()
            if not token_clean:
                return ""
            if token_clean in self.ACRONYM_WHITELIST:
                return token_clean.upper()
            if len(token_clean) <= 3 and token_clean.isalpha():
                return token_clean.upper()
            return token_clean.capitalize()

        parts = []
        for raw_part in phrase.split():
            if raw_part.upper() in self.ELEMENT_STOPWORDS:
                continue

            if "-" in raw_part:
                sub_parts = [normalize_token(sub) for sub in raw_part.split("-")]
                parts.append("-".join(filter(None, sub_parts)))
            else:
                normalized = normalize_token(raw_part)
                if normalized:
                    parts.append(normalized)
        return " ".join(parts).strip()

    def _infer_quantity(self, prefix: str) -> int:
        if not prefix:
            return 1
        match = re.search(r"(\d+)\s*$", prefix.strip())
        if match:
            try:
                return max(1, int(match.group(1)))
            except ValueError:
                return 1
        return 1

    def normalize_character_name(self, raw_name: str) -> str:
        """
        Normalize a character name by removing common screenplay annotations.

        Examples:
        - "ALICE (V.O.)" -> "ALICE"
        - "BOB (O.S.)" -> "BOB"
        - "CHARLIE (CONT'D)" -> "CHARLIE"
        - "DANA (into phone)" -> "DANA"
        - "  ERIC  " -> "ERIC"
        """
        if not raw_name:
            return ""

        # Remove common screenplay extensions in parentheses
        # V.O. = voice over, O.S. = off screen, CONT'D = continued
        name = re.sub(r'\s*\([^)]*\)\s*', '', raw_name)

        # Clean up whitespace
        name = re.sub(r'\s+', ' ', name).strip()

        # Convert to title case for consistency, but preserve all-caps if that's the style
        # Most screenplays use ALL CAPS for character names
        name = name.upper()

        return name

    def parse_location_and_time(self, slugline: str) -> Tuple[str, str]:
        # Typical slugline: "INT. HOUSE - DAY"
        parts = [segment.strip() for segment in slugline.split(" - ")]
        time_of_day = "OTHER"
        if parts:
            last = parts[-1]
            if re.search(r"\bDAY\b", last):
                time_of_day = "DAY"
            elif re.search(r"\bNIGHT\b", last):
                time_of_day = "NIGHT"
            elif re.search(r"\bINT/EXT\b", parts[0]):
                time_of_day = "INT/EXT"

        location = slugline
        location_match = re.search(r"(INT\.|EXT\.|INT/EXT\.?)\s*(.*)", slugline, re.IGNORECASE)
        if location_match:
            location = location_match.group(2)
            location = re.sub(r"\b(DAY|NIGHT|CONTINUOUS|MOMENTS LATER)\b", "", location, flags=re.IGNORECASE)
            location = location.replace("-", "").strip()
        location = location.upper()

        return location, time_of_day

    def calculate_eighths_from_pages(self, paragraphs: Iterable[dict[str, str]]) -> int | None:
        """
        Calculate scene length from actual page numbers in FDX if available.

        Returns None if page numbers are not available in the paragraphs.
        """
        page_numbers = []

        for paragraph in paragraphs:
            page_num = paragraph.get("page_number")
            if page_num:
                try:
                    page_numbers.append(int(page_num))
                except (ValueError, TypeError):
                    continue

        if not page_numbers:
            return None

        # Calculate page range
        min_page = min(page_numbers)
        max_page = max(page_numbers)

        # If scene spans multiple pages, we need to estimate eighths more precisely
        # Count how many paragraphs are on each page
        page_para_counts = {}
        for paragraph in paragraphs:
            page_num = paragraph.get("page_number")
            if page_num:
                try:
                    page_num_int = int(page_num)
                    page_para_counts[page_num_int] = page_para_counts.get(page_num_int, 0) + 1
                except (ValueError, TypeError):
                    pass

        if not page_para_counts:
            return None

        # Simple calculation: full pages + partial estimation for first/last pages
        total_eighths = 0

        if min_page == max_page:
            # Scene is on a single page - estimate based on content
            # Use the standard estimation method but return result
            return self.estimate_eighths(paragraphs)
        else:
            # Scene spans multiple pages
            # Count full pages (everything between first and last)
            full_pages = max(0, max_page - min_page - 1)
            total_eighths += full_pages * 8

            # Add eighths for first and last pages (estimate as roughly half a page each)
            # This is conservative but more accurate than pure estimation
            first_page_paras = page_para_counts.get(min_page, 0)
            last_page_paras = page_para_counts.get(max_page, 0)

            # Rough estimation: if there are paragraphs on first/last page, add eighths
            if first_page_paras > 0:
                total_eighths += 4  # Assume ~half page on first page
            if last_page_paras > 0:
                total_eighths += 4  # Assume ~half page on last page

            return max(1, total_eighths)

    def estimate_eighths(self, paragraphs: Iterable[dict[str, str]]) -> int:
        """
        Estimate scene length in eighths of a page based on paragraph content.

        Uses industry-standard screenplay formatting assumptions:
        - SCENE HEADINGs: 1 line + blank line after
        - Character names: 1 line (centered, standalone)
        - Dialogue: ~35 chars per line (narrower margins)
        - Action: ~55 chars per line (full width)
        - Parentheticals: 1 line
        - 1 page ~= 55 lines, so 1/8 page ~= 6.875 lines

        NOTE: This estimation tends to be conservative. Actual page count
        may be higher due to formatting, spacing, and page breaks.
        """
        total_lines = 0.0

        for paragraph in paragraphs:
            para_type = paragraph.get("type", "")
            text = paragraph.get("text", "")
            if not text:
                continue

            # Calculate lines based on paragraph type
            if para_type == "SCENE HEADING":
                # SCENE HEADINGs are always 1 line + blank line after
                total_lines += 2.0
            elif para_type == "CHARACTER":
                # Character names are 1 line + blank line before
                total_lines += 2.0
            elif para_type == "PARENTHETICAL":
                # Parentheticals are typically 1 line
                total_lines += 1.0
            elif para_type == "DIALOGUE":
                # Dialogue has narrower width (~35 chars per line)
                char_count = len(text)
                estimated_lines = max(1.0, char_count / 35.0)
                total_lines += estimated_lines
                # Add blank line after dialogue block
                total_lines += 1.0
            elif para_type == "ACTION":
                # Action lines use full width (~55 chars per line)
                char_count = len(text)
                estimated_lines = max(1.0, char_count / 55.0)
                total_lines += estimated_lines
                # Add blank line after action
                total_lines += 1.0
            elif para_type == "TRANSITION":
                # Transitions are 1 line + blank lines
                total_lines += 2.0
            else:
                # Default: estimate as action
                char_count = len(text)
                estimated_lines = max(1.0, char_count / 55.0)
                total_lines += estimated_lines
                total_lines += 0.5

        # Convert lines to eighths (1 page = 8 eighths)
        # Standard: 1 page ~= 55 lines, 1/8 page ~= 6.875 lines
        estimated_lines_per_eighth = 6.875
        eighths = total_lines / estimated_lines_per_eighth

        # Apply calibration multiplier to match Final Draft's actual calculations
        eighths = eighths * self.PAGE_ESTIMATION_MULTIPLIER

        # Round to nearest eighth and ensure at least 1
        eighths = max(1, round(eighths))
        return eighths

    def first_slugline(self, paragraphs: list[dict[str, str]]) -> str | None:
        for paragraph in paragraphs:
            if paragraph["type"] == "SCENE HEADING":
                return paragraph["text"]
        return None

    def clean_text(self, text: str) -> str:
        return re.sub(r"\s+", " ", text or "").strip()

    def _safe_int(self, value: str | None) -> int | None:
        if value is None:
            return None
        try:
            return int(value)
        except ValueError:
            return None

    def _safe_float(self, value: str | None) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except ValueError:
            return None

    def _parse_length(self, scene_element: ET.Element) -> int | None:
        length_eighths_value = self._safe_float(scene_element.attrib.get("LengthInEighths"))
        if length_eighths_value is not None:
            return max(1, int(round(length_eighths_value)))

        length_pages_value = self._safe_float(scene_element.attrib.get("Length"))
        if length_pages_value is not None:
            return max(1, int(round(length_pages_value * 8)))

        return None

    def _normalize_para_type(self, para_type: str | None) -> str:
        if not para_type:
            return ""
        return para_type.strip().upper()

    def _build_character_lookup(self, root: ET.Element) -> Dict[str, str]:
        lookup: Dict[str, str] = {}
        for character in root.findall(".//Character"):
            char_id = character.attrib.get("ID") or character.attrib.get("CharacterID")
            if not char_id:
                continue
            name = character.attrib.get("Name") or character.attrib.get("Character")
            if name:
                lookup[char_id] = self.clean_text(name).upper()
        return lookup

    def _extract_meta_characters(
        self, scene_element: ET.Element, character_lookup: Dict[str, str]
    ) -> List[str]:
        characters: list[str] = []
        for character in scene_element.findall(".//Characters/Character"):
            name = character.attrib.get("Name") or character.attrib.get("Character")
            if not name:
                char_id = character.attrib.get("CharacterID")
                if char_id and char_id in character_lookup:
                    name = character_lookup[char_id]
            cleaned = self.clean_text(name or "").upper()
            if cleaned:
                characters.append(cleaned)
        return characters
