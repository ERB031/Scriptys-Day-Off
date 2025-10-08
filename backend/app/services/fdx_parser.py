from __future__ import annotations

import math
import re
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from io import BytesIO
from typing import Dict, Iterable, List, Tuple
from uuid import uuid4


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


class FDXParser:
    """Parse Final Draft FDX files into structured scene metadata."""

    def parse(self, file_bytes: bytes) -> List[ParsedScene]:
        root = self._load_xml(file_bytes)
        scene_meta = self._extract_scene_meta(root)
        paragraphs, scene_order = self._collect_paragraphs(root)

        parsed_scenes: list[ParsedScene] = []
        seen_ids: set[str] = set()

        for scene_id in scene_order:
            meta = scene_meta.get(scene_id, {})
            scene_paragraphs = paragraphs.get(scene_id, [])
            slugline = meta.get("title") or self.first_slugline(scene_paragraphs)
            if not slugline:
                # Skip anything that does not look like a proper scene heading.
                continue

            clean_slugline = self.clean_text(slugline)
            location, day_night = self.parse_location_and_time(clean_slugline)

            cast = sorted({self.clean_text(p["text"]) for p in scene_paragraphs if p["type"] == "Character"})
            props = []  # Placeholder for future prop extraction.

            page_eighths = meta.get("length_eighths") or self.estimate_eighths(scene_paragraphs)
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
                )
            )

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

    def _extract_scene_meta(self, root: ET.Element) -> Dict[str, Dict[str, str | int]]:
        meta: dict[str, dict[str, str | int]] = {}
        for scene in root.findall(".//SceneProperties/Scene"):
            scene_id = scene.attrib.get("SceneID") or scene.attrib.get("ID")
            if not scene_id:
                continue
            length_eighths = self._safe_int(scene.attrib.get("LengthInEighths"))
            meta[scene_id] = {
                "id": scene_id,
                "number": scene.attrib.get("Number") or scene.attrib.get("SceneNumber"),
                "title": scene.attrib.get("Title"),
                "length_eighths": length_eighths,
            }
        return meta

    def _collect_paragraphs(
        self, root: ET.Element
    ) -> Tuple[Dict[str, list[dict[str, str]]], List[str]]:
        paragraphs: dict[str, list[dict[str, str]]] = {}
        scene_order: list[str] = []

        for para in root.findall(".//Content/Paragraph"):
            scene_id = para.attrib.get("SceneID")
            para_type = para.attrib.get("Type", "")
            text = "".join(node.text or "" for node in para.findall("Text"))
            text = self.clean_text(text)

            if not scene_id:
                # Some FDX files use Scene Heading paragraphs without SceneID.
                if para_type == "Scene Heading":
                    scene_id = str(uuid4())
                else:
                    continue

            if scene_id not in paragraphs:
                paragraphs[scene_id] = []
                scene_order.append(scene_id)

            paragraphs[scene_id].append({"type": para_type, "text": text})

        return paragraphs, scene_order

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

    def estimate_eighths(self, paragraphs: Iterable[dict[str, str]]) -> int:
        total_lines = 0.0
        for paragraph in paragraphs:
            para_type = paragraph["type"]
            text = paragraph["text"]
            if not text:
                continue

            if para_type == "Action":
                weight = 1.0
            elif para_type == "Dialogue":
                weight = 0.7
            elif para_type == "Scene Heading":
                weight = 0.4
            else:
                weight = 0.5

            char_count = len(text)
            estimated_lines = max(1.0, char_count / 45.0) * weight
            total_lines += estimated_lines

        # 1 page ≈ 54 lines, therefore 1/8 page ≈ 6.75 lines.
        eighths = max(1, math.ceil(total_lines / 6.75))
        return eighths

    def first_slugline(self, paragraphs: list[dict[str, str]]) -> str | None:
        for paragraph in paragraphs:
            if paragraph["type"] == "Scene Heading":
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
