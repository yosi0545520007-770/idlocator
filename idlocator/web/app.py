"""יישום Flask להצגת מסך טעינת קבצים וחיפוש תוצאות."""
from __future__ import annotations

import csv
import io
from dataclasses import asdict
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from flask import Flask, redirect, render_template, request, session, url_for
from jinja2.exceptions import TemplateNotFound

from ..models import Person, persons_from_dicts
from ..repository import PersonRepository, load_sample_repository
from ..service import IdentityLocator, MatchResult

# הגדרת נתיבי בסיס
# PROJECT_ROOT מצביע לשורש הפרויקט (C:\...\idlocator)
WEB_APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = WEB_APP_DIR.parents[1] # חישוב יציב של נתיב הפרויקט
TEMPLATE_FILE = PROJECT_ROOT / "data" / "people_template.csv"

# הגדרת אפליקציית Flask.
# קובץ התבנית (index.html) נטען מהתיקייה הראשית של הפרויקט.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder=str(WEB_APP_DIR))
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

    # Handle clear session request from "Clear Form" button
    if "clear" in request.args:
        session.pop("search_params", None)
        session.pop("search_results", None)
        return redirect(url_for("index"))

    locator = get_locator()

    if request.method == "POST":
        # Store search params in session to repopulate form after redirect
        search_params = {key: request.form.get(key, "").strip() for key in ["id_number", "first_name", "last_name", "street", "city", "house_number"]}
        search_params["use_soundex"] = request.form.get("use_soundex") is not None
        session["search_params"] = search_params
        
        # Handle file upload
        if "upload" in request.form and "csv_file" in request.files and request.files["csv_file"].filename:
            file = request.files["csv_file"]
            try:
                stream = io.StringIO(file.stream.read().decode("utf-8-sig"), newline="")
                reader = csv.DictReader(stream)
                # Store file content in session
                # Convert OrderedDicts to regular dicts to ensure JSON serialization
                session["people_data"] = [dict(row) for row in reader]
                session.pop("search_results", None) # Clear previous results
                locator = get_locator()
                messages.append({"text": f"קובץ '{file.filename}' נטען בהצלחה.", "type": "success"})
            except (UnicodeDecodeError, csv.Error):
                messages.append({"text": "שגיאה בתוכן הקובץ. אנא ודא שהקובץ בפורמט CSV תקין ובקידוד UTF-8.", "type": "error"})
            except Exception as e:
                logger.error(f"Error processing uploaded file: {e}")
                messages.append({"text": "אירעה שגיאה לא צפויה בעת עיבוד הקובץ.", "type": "error"})
            session["messages"] = messages
            return redirect(url_for("index"))

        # Handle reset to sample data
        elif "reset_sample" in request.form:
            if "people_data" in session:
                session.pop("people_data")
            session.pop("search_results", None) # Clear previous results
            locator = get_locator()
            messages.append({"text": "נתוני הדוגמה נטענו מחדש.", "type": "success"})
            session["messages"] = messages
            return redirect(url_for("index"))

        # Handle search (default action if not upload or reset)
        else:
            if any(value for key, value in search_params.items() if key != "use_soundex"):
                try:
                    results = _search(locator, search_params, search_params["use_soundex"])
                    # Serialize results to store in session
                    session["search_results"] = [asdict(r) for r in results]
                    if not results:
                        messages.append({"text": "לא נמצאו תוצאות עבור פרטי החיפוש שסיפקת.", "type": "info"})
                except Exception:
                    messages.append({"text": "אירעה שגיאה בעת ניסיון לבצע את החיפוש. נסה שוב מאוחר יותר.", "type": "error"})
                if messages:
                    session["messages"] = messages
            return redirect(url_for("index"))

    # On GET request, retrieve data from session
    messages = session.pop("messages", [])  # Messages should only be shown once
    search_params = session.get("search_params", {"use_soundex": True})
    results_data = session.get("search_results")
    results = [MatchResult(person=Person.from_dict(r['person']), score=r['score'], field_scores=r['field_scores']) for r in results_data] if results_data else None
    
    try:
        current_data = locator.repository.all()
        return render_template(
            "index.html",
            messages=messages,
            results=results,
            search=search_params,
            current_data=current_data,
        )
    except TemplateNotFound:
        error_msg = f"שגיאה קריטית: קובץ התבנית 'index.html' לא נמצא. ודא שהוא ממוקם בתיקייה: {app.template_folder}"
        logger.error(error_msg)
        return f"<h1>{error_msg}</h1>", 500


if __name__ == "__main__":
    # This block is for local development.
    # When deploying with a production server like Gunicorn,
    # this part is not executed.
    # Example: gunicorn "idlocator.web.app:app"
    app.run(debug=True, port=5000, host="127.0.0.1")
