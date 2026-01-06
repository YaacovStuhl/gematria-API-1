from __future__ import annotations

import unicodedata

# Standard (Mispar Hechrechi) gematria values.
_GEMATRIA_VALUES: dict[str, int] = {
    "א": 1,
    "ב": 2,
    "ג": 3,
    "ד": 4,
    "ה": 5,
    "ו": 6,
    "ז": 7,
    "ח": 8,
    "ט": 9,
    "י": 10,
    "כ": 20,
    "ל": 30,
    "מ": 40,
    "נ": 50,
    "ס": 60,
    "ע": 70,
    "פ": 80,
    "צ": 90,
    "ק": 100,
    "ר": 200,
    "ש": 300,
    "ת": 400,

    # Final forms (so we can compute without altering stored phrases).
    "ך": 20,
    "ם": 40,
    "ן": 50,
    "ף": 80,
    "ץ": 90,
}

def _is_hebrew_letter(ch: str) -> bool:
    # Hebrew block: U+0590..U+05FF
    code = ord(ch)
    return 0x0590 <= code <= 0x05FF


def normalize_phrase(phrase: str) -> str:
    """
    Normalize a user-supplied phrase for gematria computation.

    - Trims whitespace
    - Unicode-normalizes (NFKC)
    - Removes Hebrew diacritics/marks (niqqud, cantillation)
    - Removes punctuation/symbols and keeps only Hebrew letters (plus spaces)
    """
    if phrase is None:
        return ""

    # Canonicalize and trim.
    s = unicodedata.normalize("NFKC", str(phrase)).strip()

    # Drop combining marks (niqqud/cantillation are category "Mn"/"Mc").
    s = "".join(ch for ch in s if not unicodedata.category(ch).startswith("M"))

    # Keep only Hebrew letters and spaces.
    out: list[str] = []
    for ch in s:
        if ch.isspace():
            out.append(" ")
            continue
        if not _is_hebrew_letter(ch):
            continue
        if ch in _GEMATRIA_VALUES:
            out.append(ch)
    return "".join(out)


def compute_gematria(phrase: str) -> int:
    """
    Compute standard gematria (Mispar Hechrechi) for a Hebrew phrase.

    Example:
      compute_gematria("שלום") == 376
    """
    normalized = normalize_phrase(phrase)
    return sum(_GEMATRIA_VALUES.get(ch, 0) for ch in normalized)


