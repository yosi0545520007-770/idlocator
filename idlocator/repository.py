"""שכבת גישה לנתונים עבור רשומות אנשים."""
from __future__ import annotations

import importlib.resources
import csv
from pathlib import Path
from typing import Dict, Iterable, List, Optional
from .models import Person, persons_from_dicts



class PersonRepository:
    """מאגר אנשים בזיכרון, ממוטב לחיפוש מהיר לפי תעודת זהות."""

    def __init__(self, persons: Iterable[Person]):
        self._persons: List[Person] = list(persons)
        # יצירת אינדקס (מילון) לחיפוש מהיר לפי תעודת זהות.
        # פעולה זו משפרת דרמטית את הביצועים מ-O(n) ל-O(1).
        self._persons_by_id: Dict[str, Person] = {p.id_number: p for p in self._persons}

    def all(self) -> List[Person]:
        return list(self._persons)

    def find_by_id(self, id_number: str) -> Optional[Person]:
        """מציאת אדם לפי תעודת זהות באמצעות חיפוש מהיר במילון."""
        return self._persons_by_id.get(id_number.strip())

    def filter_by_city(self, city: str) -> List[Person]:
        city = city.strip().lower()
        return [person for person in self._persons if person.city.lower() == city]

    @classmethod
    def from_csv(cls, csv_path: Path) -> "PersonRepository":
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        with csv_path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            return cls(persons_from_dicts(reader))


def load_sample_repository() -> PersonRepository:
    """טעינת מאגר ברירת המחדל מהקובץ sample_people.csv."""
    # Use importlib.resources to safely access data files packaged with the application.
    # This is the modern, standard-library way and is more reliable than relative paths.
    try:
        files = importlib.resources.files("idlocator")
        with (files / "data" / "sample_people_20.csv").open("r", encoding="utf-8-sig") as f:
            return PersonRepository(persons_from_dicts(csv.DictReader(f)))
    except (FileNotFoundError, ModuleNotFoundError) as e:
        raise FileNotFoundError(f"Cannot find the sample data file: {e}") from e
