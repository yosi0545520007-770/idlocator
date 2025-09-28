"""בדיקות UI עבור ממשק ה-Flask של הפרויקט."""
from __future__ import annotations

import io
import unittest

from idlocator.web.app import app


class WebUITestCase(unittest.TestCase):
    """בדיקות ממשק משתמש ווב (Flask)."""

    def setUp(self) -> None:
        """הגדרת ה-test client של Flask."""
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False  # Disable CSRF for testing forms
        self.client = app.test_client()

    def test_index_page_loads(self) -> None:
        """בדיקה שהדף הראשי נטען בהצלחה (GET)."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Id Locator".encode("utf-8"), response.data)
        self.assertIn("חיפוש מתקדם".encode("utf-8"), response.data)

    def test_search_returns_results(self) -> None:
        """בדיקת פונקציונליות החיפוש עם נתוני הדוגמה."""
        response = self.client.post("/", data={"first_name": "אור", "last_name": "כהן"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("200000001".encode("utf-8"), response.data)  # ID of 'אור כהן'
        self.assertIn("<td>100.0</td>".encode("utf-8"), response.data)  # Perfect score

    def test_search_no_results(self) -> None:
        """בדיקה שהודעה מתאימה מוצגת כשאין תוצאות חיפוש."""
        response = self.client.post("/", data={"first_name": "משתמש", "last_name": "לאקיים"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("לא נמצאו תוצאות לחיפוש הנוכחי".encode("utf-8"), response.data)

    def test_reset_to_sample_data(self) -> None:
        """בדיקת איפוס לנתוני הדוגמה."""
        response = self.client.post("/", data={"reset_sample": "1"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("נתוני הדוגמה נטענו מחדש.".encode("utf-8"), response.data)

    def test_file_upload_success(self) -> None:
        """בדיקת העלאת קובץ CSV תקין."""
        csv_data = (
            b"id_number,first_name,last_name,street,city,house_number\n"
            b"987654321,Test,User,Python,Flask,123\n"
        )
        data = {
            "csv_file": (io.BytesIO(csv_data), "test.csv"),
        }
        response = self.client.post("/", data=data, content_type="multipart/form-data")
        self.assertEqual(response.status_code, 200)
        self.assertIn("קובץ 'test.csv' נטען בהצלחה.".encode("utf-8"), response.data)
        # Verify the new data is searchable
        search_response = self.client.post("/", data={"first_name": "Test"})
        self.assertIn("987654321".encode("utf-8"), search_response.data)

    def test_file_upload_invalid_content(self) -> None:
        """בדיקת העלאת קובץ CSV ריק או לא תקין."""
        csv_data = b"header1,header2\ninvalid,row"
        data = {
            "csv_file": (io.BytesIO(csv_data), "invalid.csv"),
        }
        response = self.client.post("/", data=data, content_type="multipart/form-data")
        self.assertEqual(response.status_code, 200)
        self.assertIn("שגיאה בתוכן הקובץ".encode("utf-8"), response.data)


if __name__ == "__main__":
    unittest.main()