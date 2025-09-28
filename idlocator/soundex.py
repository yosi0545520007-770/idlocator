"""מימוש פשוט של אלגוריתם Soundex עבור מחרוזות לטיניות."""
from __future__ import annotations

import re
from typing import Dict, Optional, Set

# מפה סטנדרטית של Soundex עבור אותיות לטיניות
_LATIN_SOUNDEX_MAP = {
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

# מפת Soundex מוצעת עבור אותיות עבריות
_HEBREW_SOUNDEX_MAP = {
    "ב": "1", "ו": "1", "פ": "1", "ף": "1",  # שפתיים
    "ג": "2", "כ": "2", "ק": "2", "ך": "2",  # וילוניים
    "ד": "3", "ט": "3", "ת": "3",  # שיניים
    "ז": "4", "ס": "4", "צ": "4", "ש": "4", "ץ": "4",  # שורקים
    "ל": "5",  # צידי
    "מ": "6", "נ": "6", "ם": "6", "ן": "6",  # אפיים
    "ר": "7",  # רוטט
    # אותיות גרוניות ואמות קריאה יקבלו קוד 0 ויותרו
    "א": "0", "ה": "0", "ח": "0", "ע": "0", "י": "0",
}

_HEBREW_SOUNDEX_MAP_VAV_AS_VOWEL = dict(_HEBREW_SOUNDEX_MAP)
_HEBREW_SOUNDEX_MAP_VAV_AS_VOWEL['ו'] = '0'

_HEBREW_SOUNDEX_VARIANT_MAPS = (_HEBREW_SOUNDEX_MAP, _HEBREW_SOUNDEX_MAP_VAV_AS_VOWEL)

# טווחי Unicode לבדיקת שפה
_HEBREW_RE = re.compile(r"[\u0590-\u05FF]")


# עוגנים לקיבוץ האות הראשונה בהתאם לצליל המרכזי
_FIRST_LETTER_ANCHORS = {
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


_HEBREW_FIRST_LETTER_ANCHORS = {
    "1": "ב",
    "2": "כ",
    "3": "ט",
    "4": "ס",
    "5": "ל",
    "6": "מ",
    "7": "ר",
}


def _is_hebrew(s: str) -> bool:
    return _HEBREW_RE.search(s) is not None


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
    """מבצע נורמליזציה לאותיות סופיות בעברית (ם -> מ, ן -> נ וכו')."""
    final_to_regular = str.maketrans("ךםןףץ", "כמנפצ")
    return text.translate(final_to_regular)


def soundex(value: str, *, length: int = 4, _soundex_map_override: Optional[Dict[str, str]] = None) -> Optional[str]:
    """החזרת קוד Soundex עבור מחרוזת נתונה."""
    if not value:
        return None

    is_hebrew = _is_hebrew(value)
    if is_hebrew:
        soundex_map = _soundex_map_override or _HEBREW_SOUNDEX_MAP
    else:
        soundex_map = _soundex_map_override or _LATIN_SOUNDEX_MAP

    # הסרת תווים שאינם אותיות
    # עבור לטינית, נמיר לאותיות גדולות. עבור עברית, נשאיר כפי שזה.
    if is_hebrew:
        # נורמליזציה של אותיות סופיות לפני הקידוד
        value = _normalize_hebrew_final_letters(value)
    processed_value = value if is_hebrew else value.upper()
    filtered = [char for char in processed_value if char.isalpha()]

    if not filtered:
        return None

    first_letter = filtered[0]
    # עבור עברית, אין צורך בקינון האות הראשונה
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
        if digit != "0":  # התעלם מאותיות שקטות
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
            if mapping is not _HEBREW_SOUNDEX_MAP and not _has_significant_digit(code):
                continue
            codes.add(code)
        return codes
    code = soundex(value, length=length)
    if code:
        codes.add(code)
    return codes


def compare_soundex(value_a: str, value_b: str, *, length: int = 4) -> bool:
    """בדיקת שוויון בין קודי Soundex של שתי מחרוזות."""
    codes_a = _soundex_codes(value_a, length)
    codes_b = _soundex_codes(value_b, length)
    if not codes_a or not codes_b:
        return False
    return bool(codes_a & codes_b)
