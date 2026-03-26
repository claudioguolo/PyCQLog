from __future__ import annotations

import re
from dataclasses import dataclass

from pycqlog.domain.awards_data import AWARD_RULES


_PORTABLE_SUFFIXES = {
    "P",
    "M",
    "MM",
    "AM",
    "A",
    "QRP",
    "LH",
    "MAR",
    "MOBILE",
    "PORTABLE",
}
_SORTED_RULES = sorted(AWARD_RULES, key=lambda item: len(item[0]), reverse=True)


@dataclass(frozen=True, slots=True)
class AwardInfo:
    entity: str = ""
    cq_zone: int | None = None
    wpx_prefix: str = ""
    matched_prefix: str = ""
    reliable: bool = False


def resolve_awards(callsign: str) -> AwardInfo:
    base_segment = _base_callsign_segment(callsign)
    if not base_segment:
        return AwardInfo()

    operating_prefix = _operating_prefix_segment(callsign, base_segment)
    matched_prefix = ""
    entity = ""
    cq_zone: int | None = None

    for candidate in _entity_candidates(operating_prefix, base_segment):
        match = _match_rule(candidate)
        if match is None:
            continue
        matched_prefix, entity, cq_zone = match
        break

    return AwardInfo(
        entity=entity,
        cq_zone=cq_zone,
        wpx_prefix=extract_wpx_prefix(base_segment),
        matched_prefix=matched_prefix,
        reliable=bool(entity),
    )


def extract_wpx_prefix(callsign: str) -> str:
    normalized = _base_callsign_segment(callsign)
    if not normalized:
        return ""
    match = re.match(r"^([A-Z]+[0-9]+[A-Z]*)", normalized)
    if match:
        return match.group(1)
    fallback = re.match(r"^([A-Z]+[0-9]+)", normalized)
    if fallback:
        return fallback.group(1)
    return normalized[: min(4, len(normalized))]


def infer_dxcc_entity(callsign: str) -> str:
    return resolve_awards(callsign).entity


def infer_cq_zone(callsign: str) -> int | None:
    return resolve_awards(callsign).cq_zone


def _entity_candidates(operating_prefix: str, base_segment: str) -> list[str]:
    candidates: list[str] = []
    for item in (operating_prefix, base_segment):
        if item and item not in candidates:
            candidates.append(item)
    return candidates


def _match_rule(segment: str) -> tuple[str, str, int | None] | None:
    for prefix, entity, zone in _SORTED_RULES:
        if segment.startswith(prefix):
            return prefix, entity, zone
    return None


def _base_callsign_segment(callsign: str) -> str:
    segments = _meaningful_segments(callsign)
    if not segments:
        return ""
    with_digits = [segment for segment in segments if any(char.isdigit() for char in segment)]
    if with_digits:
        return max(with_digits, key=len)
    return max(segments, key=len)


def _operating_prefix_segment(callsign: str, base_segment: str) -> str:
    raw_segments = _meaningful_segments(callsign)
    if len(raw_segments) < 2:
        return ""
    for segment in raw_segments:
        if segment == base_segment:
            break
        if len(segment) <= 4:
            return segment
    return ""


def _meaningful_segments(callsign: str) -> list[str]:
    normalized = callsign.strip().upper()
    if not normalized:
        return []
    segments = [segment for segment in normalized.split("/") if segment]
    return [segment for segment in segments if segment not in _PORTABLE_SUFFIXES]
