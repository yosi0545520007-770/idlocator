"""מודלים בסיסיים של היישום."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List


@dataclass(frozen=True)
class Person:
    """ייצוג פשוט של רשומת אדם."""

    id_number: str
    first_name: str
    last_name: str
    street: str
    city: str
    house_number: str

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def full_address(self) -> str:
        return f"{self.street} {self.house_number}, {self.city}".strip(", ")

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "Person":
        return cls(
            id_number=str(data.get("id_number", "")).strip(),
            first_name=str(data.get("first_name", "")).strip(),
            last_name=str(data.get("last_name", "")).strip(),
            street=str(data.get("street", "")).strip(),
            city=str(data.get("city", "")).strip(),
            house_number=str(data.get("house_number", "")).strip(),
        )


def persons_from_dicts(items: Iterable[Dict[str, str]]) -> List[Person]:
    """המרת רשימת מילונים לרשימת אובייקטי Person."""
    return [Person.from_dict(item) for item in items]
