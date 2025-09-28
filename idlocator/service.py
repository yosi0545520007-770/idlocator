﻿"""לוגיקה עיקרית של חיפוש והתאמת זהות."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, Iterable, List, Optional

from .models import Person
from .repository import PersonRepository, load_sample_repository
from .soundex import compare_soundex

@dataclass(frozen=True)
class MatchResult:
    """מייצג תוצאה משוקללת של חיפוש."""

    person: Person
    score: float
    field_scores: Dict[str, float]

_FIELD_WEIGHTS = {
    "first_name": 3.0,
    "last_name": 3.0,
    "street": 2.0,
    "city": 1.5,
    "house_number": 1.5,
}

# מילון כינויים ושמות נפוצים בעברית
_NICKNAME_MAP: Dict[str, List[str]] = {
    "אבי": ["אברהם"],
    "איציק": ["יצחק", "יחזקאל"],
    "אלי": ["אליהו", "אליעזר"],
    "בני": ["בנימין"],
    "גבי": ["גבריאל"],
    "דודי": ["דוד"],
    "דני": ["דניאל"],
    "יענקל'ה": ["יעקב"],
    "יוסי": ["יוסף"],
    "מיקי": ["מיכאל", "מיכל"],
    "מוטי": ["מרדכי"],
    "צחי": ["יצחק"],
    "רפי": ["רפאל"],
    "שוקי": ["יהושע"],
    "שי": ["ישעיהו"],
    "שמוליק": ["שמואל"],
}

# בניית מפה דו-כיוונית לחיפוש כינויים יעיל
_REVERSE_NICKNAME_MAP: Dict[str, List[str]] = {}
for nickname, full_names in _NICKNAME_MAP.items():
    for full_name in full_names:
        if full_name not in _REVERSE_NICKNAME_MAP:
            _REVERSE_NICKNAME_MAP[full_name] = []
        _REVERSE_NICKNAME_MAP[full_name].append(nickname)

class IdentityLocator:
    """שירות חיפוש זהויות על בסיס נתונים מובנים."""

    def __init__(self, repository: PersonRepository):
        self.repository = repository

    def find_by_id(self, id_number: str) -> Optional[Person]:
        return self.repository.find_by_id(id_number)

    def search(
        self,
        *,
        id_number: Optional[str] = None,  # חיפוש לפי מספר זהות
        first_name: Optional[str] = None,  # חיפוש לפי שם פרטי
        last_name: Optional[str] = None,  # חיפוש לפי שם משפחה
        street: Optional[str] = None,
        city: Optional[str] = None,
        house_number: Optional[str] = None,
        use_soundex: bool = True,
    ) -> List[MatchResult]:
        """מחזירה רשימת התאמות משוקללות עבור החיפוש."""
        if id_number:
            person = self.find_by_id(id_number)
            if not person:
                return []
            return [MatchResult(person=person, score=100.0, field_scores={"id_number": 100.0})]

        # אסטרטגיית סינון מוקדם לשיפור ביצועים:
        # 1. התחל עם כל האנשים.
        # 2. אם סופקה עיר, סנן תחילה לפיה כדי לצמצם את קבוצת המועמדים.
        #    זהו שיפור ביצועים משמעותי עבור קבצים גדולים.
        candidates = self.repository.all()
        if city and city.strip():
            candidates = self.repository.filter_by_city(city)

        matches: List[MatchResult] = []
        for person in candidates:
            result = _evaluate_person(
                person,
                first_name=first_name,
                last_name=last_name,
                street=street,
                city=city,
                house_number=house_number,
                use_soundex=use_soundex,
            )
            if result is not None:
                matches.append(result)

        matches.sort(key=lambda item: item.score, reverse=True)
        return matches

def load_default_repository() -> PersonRepository:
    """פונקציית עזר לטעינת מאגר ברירת מחדל."""
    return load_sample_repository()

def _evaluate_person(
    person: Person,
    *,
    first_name: Optional[str],
    last_name: Optional[str],
    street: Optional[str],
    city: Optional[str],
    house_number: Optional[str],
    use_soundex: bool,
) -> Optional[MatchResult]:
    field_scores: Dict[str, float] = {}
    total_weight = 0.0
    weighted_sum = 0.0

    def handle_text(field_name: str, query: Optional[str], value: str) -> bool:
        nonlocal total_weight, weighted_sum
        if query and query.strip():
            weight = _FIELD_WEIGHTS[field_name]
            score = _score_text_field(query, value, use_soundex)
            field_scores[field_name] = round(score * 100, 2)
            total_weight += weight
            if score <= 0.0:
                return False
            weighted_sum += score * weight
        return True

    if not handle_text("first_name", first_name, person.first_name):
        return None
    if not handle_text("last_name", last_name, person.last_name):
        return None
    if not handle_text("street", street, person.street):
        return None
    if not handle_text("city", city, person.city):
        return None

    if house_number and house_number.strip():
        weight = _FIELD_WEIGHTS["house_number"]
        score = _score_house_number(house_number, person.house_number)
        field_scores["house_number"] = round(score * 100, 2)
        total_weight += weight
        if score <= 0.0:
            return None
        weighted_sum += score * weight

    final_score = round((weighted_sum / total_weight) * 100, 2) if total_weight else 0.0
    return MatchResult(person=person, score=final_score, field_scores=field_scores)

def _normalize_for_phonetic_search(text: str) -> str:
    """מבצע נורמליזציה פונטית בסיסית להשוואה מדויקת יותר."""
    text = text.casefold()
    # החלפת אותיות עם צליל דומה
    replacements = str.maketrans({
        'ט': 'ת', 'כ': 'ק', 'ס': 'ש', 'ב': 'ו', 'צ': 'ז',
        'א': '', 'ה': '', 'י': ''  # הסרת אמות קריאה נפוצות
    })
    return text.translate(replacements)

def _levenshtein_similarity(s1: str, s2: str) -> float:
    """מחשב את יחס הדמיון של Levenshtein בין שתי מחרוזות."""
    if not s1 and not s2:
        return 1.0
    if not s1 or not s2:
        return 0.0

    m, n = len(s1), len(s2)
    if m < n:
        s1, s2 = s2, s1
        m, n = n, m

    previous_row = list(range(n + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    distance = previous_row[n]
    return 1.0 - (distance / m)


def _score_text_field(query: str, value: str, use_soundex: bool) -> float:
    query = (query or "").strip()
    value = (value or "").strip()
    if not query or not value:
        return 0.0

    query_lower = query.casefold()
    value_lower = value.casefold()

    if query_lower == value_lower:
        return 1.0

    # בדיקה דו-כיוונית ויעילה להתאמת כינויים
    if (query_lower in _NICKNAME_MAP and value_lower in _NICKNAME_MAP[query_lower]) or \
       (query_lower in _REVERSE_NICKNAME_MAP and value_lower in _REVERSE_NICKNAME_MAP[query_lower]):
        return 0.9

    if value_lower.startswith(query_lower):
        return 0.85
    # בדיקה חדשה: התאמה פונטית "חזקה" עם ציון גבוה יותר
    if _normalize_for_phonetic_search(query) == _normalize_for_phonetic_search(value):
        return 0.88

    # בדיקה חדשה: התאמה לפי דמיון Levenshtein (טוב לטעויות הקלדה)
    lev_similarity = _levenshtein_similarity(query_lower, value_lower)
    if lev_similarity >= 0.8:
        return 0.8

    if use_soundex and compare_soundex(query, value):
        return 0.75

    if query_lower in value_lower:
        return 0.65
    return 0.0

def _score_house_number(query: str, value: str) -> float:
    """מעניק ציון להתאמה בין מספרי בתים, עם תמיכה בהתאמה חלקית."""
    query_s = (query or "").strip()
    value_s = (value or "").strip()

    if not query_s or not value_s:
        return 0.0

    # התאמה מדויקת היא הטובה ביותר
    if query_s == value_s:
        return 1.0

    # התאמה חלקית (למשל, חיפוש "12" מול "12א")
    if value_s.startswith(query_s) or query_s.startswith(value_s):
        return 0.95  # ציון גבוה אך לא מושלם
    return 0.0
