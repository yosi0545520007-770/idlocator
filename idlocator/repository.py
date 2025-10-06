﻿"""שכבת גישה לנתונים עבור רשומות אנשים."""
from __future__ import annotations

import csv
from pathlib import Path
import pkg_resources
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
    # Use pkg_resources to safely access data files packaged with the application.
    # This is more reliable than relative path calculations, especially in containers.
    resource_path = "data/sample_people_20.csv"
    if not pkg_resources.resource_exists("idlocator", resource_path):
        raise FileNotFoundError(f"Cannot find the sample data file at: {resource_path}")
    
    stream = pkg_resources.resource_stream("idlocator", resource_path)
    return PersonRepository(persons_from_dicts(csv.DictReader(stream.read().decode("utf-8-sig").splitlines())))
