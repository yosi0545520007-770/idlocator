"""ממשק שורת פקודה עבור פרויקט איתור זהות."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Sequence

from .repository import PersonRepository, load_sample_repository
from .service import IdentityLocator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="איתור זהות לפי כתובת ותעודת זהות")
    parser.add_argument("--id", dest="id_number", help="מספר תעודת זהות לחיפוש")
    parser.add_argument("--first-name", help="שם פרטי לחיפוש")
    parser.add_argument("--last-name", help="שם משפחה לחיפוש")
    parser.add_argument("--street", help="שם רחוב לחיפוש")
    parser.add_argument("--city", help="שם העיר לחיפוש")
    parser.add_argument("--house-number", help="מספר בית לחיפוש")
    parser.add_argument(
        "--no-soundex",
        action="store_true",
        help="ביטול שימוש בהתאמת Soundex",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        help="נתיב לקובץ CSV מותאם אישית של רשומות אנשים",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        repository = (
            PersonRepository.from_csv(args.csv) if args.csv else load_sample_repository()
        )
    except FileNotFoundError as e:
        print(f"שגיאה: הקובץ לא נמצא - {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"שגיאה לא צפויה בעת טעינת הקובץ: {e}", file=sys.stderr)
        return 1
    locator = IdentityLocator(repository)

    matches = locator.search(
        id_number=args.id_number,
        first_name=args.first_name,
        last_name=args.last_name,
        street=args.street,
        city=args.city,
        house_number=args.house_number,
        use_soundex=not args.no_soundex,
    )

    if not matches:
        print("לא נמצאו תוצאות")
        return 1

    for match in matches:
        person = match.person
        print("-" * 40)
        print(f"מספר זהות: {person.id_number}")
        print(f"שם פרטי: {person.first_name}")
        print(f"שם משפחה: {person.last_name}")
        print(f"רחוב: {person.street}")
        print(f"מספר בית: {person.house_number}")
        print(f"עיר: {person.city}")
        print(f"כתובת מלאה: {person.full_address}")
        print(f"ציון התאמה: {match.score:.1f}%")
        if match.field_scores:
            score_details = ", ".join(
                f"{name}: {score:.0f}%" for name, score in match.field_scores.items()
            )
            print(f"פירוט הניקוד: ({score_details})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
