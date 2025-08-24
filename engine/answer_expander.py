from __future__ import annotations

from typing import Dict, List, Tuple


def build_priorities(profile: Dict) -> List[str]:
    priorities: List[str] = []
    concerns = profile.get("concerns") or []
    if "barrier" in concerns or profile.get("dehydrated"):
        priorities.append("barrier_repair")
    if "acne" in concerns:
        priorities.append("acne_control")
    if "pigmentation" in concerns:
        priorities.append("even_tone")
    if "redness" in concerns:
        priorities.append("calming")
    if not priorities:
        priorities.append("balanced_routine")
    return priorities


def build_tldr_and_full(result_text: str) -> Tuple[str, str]:
    # TL;DR — первые 5-8 строк, FULL — весь текст
    lines = [l for l in (result_text or "").splitlines() if l.strip()]
    tldr = "\n".join(lines[:8])
    full = result_text
    return tldr, full


def expand(profile: Dict, rendered_text: str, products: Dict) -> Dict:
    priorities = build_priorities(profile)
    tl_dr, full = build_tldr_and_full(rendered_text)
    warnings: List[str] = []
    if profile.get("sensitivity") == "high":
        warnings.append("introduce_slowly")
    if "texture" in (profile.get("concerns") or []):
        warnings.append("photosensitivity_acids")
    return {
        "profile": profile,
        "priorities": priorities,
        "routines": {},
        "compatibility": {},
        "products": products,
        "warnings": warnings,
        "tl_dr": tl_dr,
        "full_text": full,
    }
