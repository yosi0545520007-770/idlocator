"""Soundex helpers for Hebrew and Latin text."""
from __future__ import annotations

import re
from typing import Dict, Optional, Set

# Standard Soundex map for Latin letters (same as traditional implementation).
_LATIN_SOUNDEX_MAP: Dict[str, str] = {
    "B": "1",
    "F": "1",
    "P": "1",
    "V": "1",
    "C": "2",
    "G": "2",
    "J": "2",
    "K": "2",
    "Q": "2",
    "S": "2",
    "X": "2",
    "Z": "2",
    "D": "3",
    "T": "3",
    "L": "4",
    "M": "5",
    "N": "5",
    "R": "6",
}

# Hebrew consonant groupings ? see comments for the linguistic intuition.
_IMPROVED_HEBREW_SOUNDEX_MAP: Dict[str, str] = {
    # Labials ? ?, ?, ?, ?, ?, ?
    "ב": "1",  # ?
    "ו": "1",  # ?
    "פ": "1",  # ?
    "ף": "1",  # ?
    "מ": "1",  # ?
    "ם": "1",  # ?
    # Velars / gutturals ? ?, ?, ?, ?, ?
    "ג": "2",  # ?
    "ק": "2",  # ?
    "כ": "2",  # ?
    "ך": "2",  # ?
    "ח": "2",  # ?
    # Dentals ? ?, ?, ?
    "ד": "3",  # ?
    "ט": "3",  # ?
    "ת": "3",  # ?
    # Sibilants ? ?, ?, ?, ?, ?
    "ז": "4",  # ?
    "ס": "4",  # ?
    "צ": "4",  # ?
    "ץ": "4",  # ?
    "ש": "4",  # ?
    # Laterals ? ?
    "ל": "5",  # ?
    # Nasals ? ?, ?
    "נ": "6",  # ?
    "ן": "6",  # ?
    # Rhotic ? ?
    "ר": "7",  # ?
    # Letters that often behave like vowels.
    "א": "0",  # ?
    "ה": "0",  # ?
    "י": "0",  # ?
    "ע": "2",  # ? (treated as guttural by default)
}

# Variants: treat ? (vav) or ? (ayin) as vowels when they serve as matres lectionis.
_IMPROVED_HEBREW_SOUNDEX_MAP_VAV_AS_VOWEL = dict(_IMPROVED_HEBREW_SOUNDEX_MAP)
_IMPROVED_HEBREW_SOUNDEX_MAP_VAV_AS_VOWEL["ו"] = "0"  # ?

_IMPROVED_HEBREW_SOUNDEX_MAP_AYIN_AS_VOWEL = dict(_IMPROVED_HEBREW_SOUNDEX_MAP)
_IMPROVED_HEBREW_SOUNDEX_MAP_AYIN_AS_VOWEL["ע"] = "0"  # ?
_IMPROVED_HEBREW_SOUNDEX_MAP_VAV_AYIN_AS_VOWEL = dict(_IMPROVED_HEBREW_SOUNDEX_MAP_VAV_AS_VOWEL)
_IMPROVED_HEBREW_SOUNDEX_MAP_VAV_AYIN_AS_VOWEL["\u05e2"] = "0"  # ?

_HEBREW_SOUNDEX_VARIANT_MAPS = (
    _IMPROVED_HEBREW_SOUNDEX_MAP,
    _IMPROVED_HEBREW_SOUNDEX_MAP_VAV_AS_VOWEL,
    _IMPROVED_HEBREW_SOUNDEX_MAP_AYIN_AS_VOWEL,
    _IMPROVED_HEBREW_SOUNDEX_MAP_VAV_AYIN_AS_VOWEL,
)

# Unicode range that covers Hebrew letters (including niqqud if present).
_HEBREW_RE = re.compile(r"[֐-׿]")

# Anchor noisy first letters for Latin words to traditional Soundex letters.
_FIRST_LETTER_ANCHORS: Dict[str, str] = {
    "B": "B",
    "F": "B",
    "P": "B",
    "V": "B",
    "C": "C",
    "G": "C",
    "J": "C",
    "K": "C",
    "Q": "C",
    "S": "C",
    "X": "C",
    "Z": "C",
    "D": "D",
    "T": "D",
    "L": "L",
    "M": "M",
    "N": "M",
    "R": "R",
}

_HEBREW_FIRST_LETTER_ANCHORS: Dict[str, str] = {
    "1": "ב",  # ?
    "2": "כ",  # ?
    "3": "ד",  # ?
    "4": "ס",  # ?
    "5": "ל",  # ?
    "6": "נ",  # ?
    "7": "ר",  # ?
}

_HEBREW_PREFIX_LETTERS = "\u05d5\u05d4\u05d1\u05dc"  # ?, ?, ?, ?


def _is_hebrew(value: str) -> bool:
    return bool(value) and _HEBREW_RE.search(value) is not None


def _encode(char: str, soundex_map: Dict[str, str]) -> str:
    return soundex_map.get(char, "0")


def _has_significant_digit(code: str) -> bool:
    return any(char != "0" for char in code[1:])


def _canonical_first_letter(letter: str) -> str:
    return _FIRST_LETTER_ANCHORS.get(letter, letter)


def _canonical_hebrew_first_letter(letter: str, soundex_map: Dict[str, str]) -> str:
    digit = _encode(letter, soundex_map)
    if digit == "0":
        return letter
    return _HEBREW_FIRST_LETTER_ANCHORS.get(digit, letter)


def _normalize_hebrew_final_letters(text: str) -> str:
    """Convert final Hebrew letters (?, ?, ?, ?, ?) to their standard form."""
    final_to_regular = str.maketrans(
        {
            "ך": "כ",  # ? -> ?
            "ם": "מ",  # ? -> ?
            "ן": "נ",  # ? -> ?
            "ף": "פ",  # ? -> ?
            "ץ": "צ",  # ? -> ?
        }
    )
    return text.translate(final_to_regular)


def _strip_hebrew_prefixes(text: str) -> str:
    """Remove common one-letter prefixes (e.g. ?, ?, ?, ?) when there is more core text."""
    if len(text) > 2 and text[0] in _HEBREW_PREFIX_LETTERS:
        return text[1:]
    return text


def soundex(value: str, *, length: int = 4, _soundex_map_override: Optional[Dict[str, str]] = None) -> Optional[str]:
    """Return a Soundex code for the given string."""
    if not value:
        return None

    is_hebrew = _is_hebrew(value)
    soundex_map: Dict[str, str]
    if is_hebrew:
        soundex_map = _soundex_map_override or _IMPROVED_HEBREW_SOUNDEX_MAP
    else:
        soundex_map = _soundex_map_override or _LATIN_SOUNDEX_MAP

    if is_hebrew:
        value = _normalize_hebrew_final_letters(value)
        value = _strip_hebrew_prefixes(value)
        processed_value = value
    else:
        processed_value = value.upper()

    filtered = [char for char in processed_value if char.isalpha()]
    if not filtered:
        return None

    first_letter = filtered[0]
    if is_hebrew:
        first_letter = _canonical_hebrew_first_letter(first_letter, soundex_map)
    else:
        first_letter = _canonical_first_letter(first_letter)

    code = [first_letter]
    prev_digit = _encode(first_letter, soundex_map)

    for char in filtered[1:]:
        digit = _encode(char, soundex_map)
        if digit == prev_digit:
            continue
        if digit != "0":
            code.append(digit)
        prev_digit = digit

    return "".join(code)[:length].ljust(length, "0")


def _soundex_codes(value: str, length: int) -> Set[str]:
    codes: Set[str] = set()
    if not value:
        return codes

    if _is_hebrew(value):
        for mapping in _HEBREW_SOUNDEX_VARIANT_MAPS:
            code = soundex(value, length=length, _soundex_map_override=mapping)
            if not code:
                continue
            if mapping is not _IMPROVED_HEBREW_SOUNDEX_MAP and not _has_significant_digit(code):
                continue
            codes.add(code)
        return codes

    code = soundex(value, length=length)
    if code:
        codes.add(code)
    return codes


def compare_soundex(value_a: str, value_b: str, *, length: int = 4) -> bool:
    """Return True when the Soundex codes of the two strings intersect."""
    codes_a = _soundex_codes(value_a, length)
    codes_b = _soundex_codes(value_b, length)
    if not codes_a or not codes_b:
        return False
    return bool(codes_a & codes_b)
