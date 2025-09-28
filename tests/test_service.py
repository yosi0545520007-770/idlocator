import unittest

from idlocator.models import Person
from idlocator.repository import PersonRepository
from idlocator.service import IdentityLocator, MatchResult
from idlocator.soundex import compare_soundex, soundex


class IdentityLocatorTests(unittest.TestCase):
    def setUp(self) -> None:
        # יצירת מאגר נתונים מדומה בזיכרון עבור הבדיקות
        mock_people = [
            Person(id_number="200000001", first_name="אור", last_name="כהן", street="הרצל", city="תל אביב", house_number="12"),
            Person(id_number="200000002", first_name="טל", last_name="לוי", street="ביאליק", city="חיפה", house_number="5"),
            Person(id_number="200000003", first_name="יעל", last_name="שחר", street="אחד העם", city="ירושלים", house_number="10"),
        ]
        self.repository = PersonRepository(mock_people)
        self.locator = IdentityLocator(self.repository)

    def test_find_by_id_returns_person(self) -> None:
        # בדיקה מול נתונים מקובץ sample_people_20.csv
        person = self.locator.find_by_id("200000001")
        self.assertIsNotNone(person)
        self.assertEqual(person.full_name, "אור כהן")

    def test_search_by_name_with_soundex(self) -> None:
        # בדיקת חיפוש פונטי בעברית לפי שם משפחה
        results = self.locator.search(last_name="כהן", use_soundex=True)
        self.assertEqual(len(results), 1)
        match = results[0]
        self.assertEqual(match.person.last_name, "כהן")
        self.assertGreaterEqual(match.score, 50.0)

    def test_search_by_first_and_last_name(self) -> None:
        # בדיקת חיפוש לפי שם פרטי ושם משפחה
        results = self.locator.search(first_name="אור", last_name="כהן")
        self.assertEqual(len(results), 1)
        match = results[0]
        self.assertEqual(match.person.id_number, "200000001")
        self.assertAlmostEqual(match.score, 100.0)

    def test_search_by_address(self) -> None:
        # בדיקת חיפוש כתובת מלאה
        results = self.locator.search(street="ביאליק", use_soundex=True)
        self.assertEqual(len(results), 1)
        match = results[0]
        self.assertEqual(match.person.id_number, "200000002")
        self.assertAlmostEqual(match.score, 100.0)

    def test_search_by_address_with_house_number(self) -> None:
        results = self.locator.search(street="הרצל", house_number="12")
        self.assertEqual(len(results), 1)
        match = results[0]
        self.assertEqual(match.person.id_number, "200000001")
        self.assertAlmostEqual(match.score, 100.0)


class SoundexTests(unittest.TestCase):
    def test_soundex_basic(self) -> None:
        self.assertEqual(soundex("Cohen"), soundex("Kohen"))

    def test_compare_soundex(self) -> None:
        self.assertTrue(compare_soundex("Tel-Aviv", "Tel Aviv"))

    def test_soundex_hebrew(self) -> None:
        """בדיקת תקינות אלגוריתם Soundex עבור השפה העברית."""
        # 1. בדיקת אותיות עם צליל דומה
        self.assertTrue(compare_soundex("כהן", "קהן"), "כ' ו-'ק' צריכות להיות שוות ערך")
        self.assertTrue(compare_soundex("טסט", "תסת"), "ט' ו-'ת' צריכות להיות שוות ערך")
        self.assertTrue(compare_soundex("יצחק", "יסחק"), "צ' ו-'ס' צריכות להיות שוות ערך")

        # 2. בדיקת התעלמות מאותיות שקטות/אמות קריאה
        self.assertTrue(compare_soundex("אבי", "אוי"), "ב' ו-'ו' שוות ערך, 'י' צריכה להיות מיוצגת באופן דומה או להתעלם ממנה")
        self.assertTrue(compare_soundex("משה", "מושה"), "התעלמות מאם קריאה 'ו'")

        # 3. בדיקה שלילית - מילים עם צליל שונה
        self.assertFalse(compare_soundex("לוי", "כהן"), "מילים שונות לא צריכות להיות תואמות")

        # 4. בדיקת התעלמות מניקוד
        self.assertTrue(compare_soundex("מֹשֶׁה", "משה"), "האלגוריתם צריך להתעלם מניקוד")

        # 5. בדיקת התאמה חלקית (אות ראשונה שונה, המשך זהה)
        self.assertTrue(compare_soundex("שמעון", "סימון"), "התאמה על בסיס שאר האותיות (מלבד הראשונה)")

        # 6. בדיקת אותיות סופיות
        self.assertTrue(compare_soundex("שם", "שמ"), "אות סופית 'ם' צריכה להיות שוות ערך ל-'מ'")
        self.assertTrue(compare_soundex("ארץ", "ארצ"), "אות סופית 'ץ' צריכה להיות שוות ערך ל-'צ'")


if __name__ == "__main__":
    unittest.main()
