"""יישום Flask להצגת מסך טעינת קבצים וחיפוש תוצאות."""
from __future__ import annotations

import csv
import io
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from flask import Flask, render_template, request, session
from jinja2.exceptions import TemplateNotFound

# In a real-world scenario, you might use a more robust session management.
# For this project, Flask's default client-side session is sufficient.
from ..models import persons_from_dicts
from ..repository import PersonRepository, load_sample_repository
from ..service import IdentityLocator

# הגדרת נתיבי בסיס
# PROJECT_ROOT מצביע לשורש הפרויקט (C:\...\idlocator)
WEB_APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = WEB_APP_DIR.parents[1]
TEMPLATE_FOLDER_PATH = PROJECT_ROOT
TEMPLATE_FILE = PROJECT_ROOT / "data" / "people_template.csv"

# הגדרת אפליקציית Flask.
# קבצי התבניות (HTML) נטענים מהתיקייה 'idlocator/web/templates'.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder=str(TEMPLATE_FOLDER_PATH))
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10MB
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'  # Needed for session management

def get_locator() -> IdentityLocator:
    """Creates an IdentityLocator based on data stored in the user's session."""
    if "people_data" in session:
        # Data from an uploaded file is stored in the session
        repo = PersonRepository(persons_from_dicts(session["people_data"]))
    else:
        # Default to the sample repository
        repo = load_sample_repository()
    return IdentityLocator(repo)


def _search(locator: IdentityLocator, params: Dict[str, Any], use_soundex: bool) -> List[Any]:
    results = locator.search(
        id_number=params.get("id_number") or None,
        first_name=params.get("first_name") or None,
        last_name=params.get("last_name") or None,
        street=params.get("street") or None,
        city=params.get("city") or None,
        house_number=params.get("house_number") or None,
        use_soundex=use_soundex,
    )
    return results


@app.route("/", methods=["GET", "POST"])
def index() -> str:
    messages: List[Dict[str, str]] = []
    results: Optional[List[Any]] = None
    locator = get_locator()

    search_params = {
        "id_number": "",
        "first_name": "",
        "last_name": "",
        "street": "",
        "city": "",
        "house_number": "",
        "use_soundex": True,
    }

    if request.method == "POST":
        # Handle file upload
        if "csv_file" in request.files and request.files["csv_file"].filename:
            file = request.files["csv_file"]
            try:
                stream = io.StringIO(file.stream.read().decode("utf-8-sig"), newline="")
                reader = csv.DictReader(stream)
                # Store file content in session
                session["people_data"] = list(reader)
                # Re-create locator with new data
                locator = get_locator()
                messages.append({"text": f"קובץ '{file.filename}' נטען בהצלחה.", "type": "success"})
            except (UnicodeDecodeError, csv.Error):
                messages.append({"text": "שגיאה בתוכן הקובץ. אנא ודא שהקובץ בפורמט CSV תקין ובקידוד UTF-8.", "type": "error"})
            except Exception as e:
                logger.error(f"Error processing uploaded file: {e}")
                messages.append({"text": "אירעה שגיאה לא צפויה בעת עיבוד הקובץ.", "type": "error"})

        # Handle reset to sample data
        elif "reset_sample" in request.form:
            if "people_data" in session:
                session.pop("people_data")
            locator = get_locator()
            messages.append({"text": "נתוני הדוגמה נטענו מחדש.", "type": "success"})

        # Handle search
        search_params.update({
            "id_number": request.form.get("id_number", "").strip(),
            "first_name": request.form.get("first_name", "").strip(),
            "last_name": request.form.get("last_name", "").strip(),
            "street": request.form.get("street", "").strip(),
            "city": request.form.get("city", "").strip(),
            "house_number": request.form.get("house_number", "").strip(),
        })
        use_soundex = request.form.get("use_soundex") is not None
        search_params["use_soundex"] = use_soundex

        if any(value for key, value in search_params.items() if key != "use_soundex"):
            try:
                results = _search(locator, search_params, use_soundex)
            except Exception:
                messages.append({"text": "אירעה שגיאה לא צפויה בעת ביצוע החיפוש.", "type": "error"})

    try:
        return render_template(
            "index.html",
            messages=messages,
            results=results,
            search=search_params,
        )
    except TemplateNotFound:
        error_msg = "שגיאה קריטית: קובץ התבנית 'index.html' לא נמצא. אנא ודא שהוא ממוקם בנתיב: 'idlocator/web/templates/index.html'"
        logger.error(error_msg)
        return f"<h1>{error_msg}</h1>", 500


if __name__ == "__main__":
    # This block is for local development.
    # When deploying with a production server like Gunicorn,
    # this part is not executed.
    # Example: gunicorn "idlocator.web.app:app"
    app.run(debug=True, port=5000, host="127.0.0.1")
