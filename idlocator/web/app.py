"""יישום Flask להצגת מסך טעינת קבצים וחיפוש תוצאות."""
from __future__ import annotations

import base64
import binascii
import csv
import io
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from flask import Flask, redirect, render_template, request, url_for
from jinja2.exceptions import TemplateNotFound

from ..models import Person, persons_from_dicts
from ..repository import PersonRepository, load_sample_repository
from ..service import IdentityLocator, MatchResult

WEB_APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = WEB_APP_DIR.parents[1]
TEMPLATE_FILE = PROJECT_ROOT / "data" / "people_template.csv"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder=str(WEB_APP_DIR))
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10MB


def _encode_people_data(rows: List[Dict[str, str]]) -> str:
    if not rows:
        return ""
    payload = json.dumps(rows, ensure_ascii=False)
    return base64.b64encode(payload.encode("utf-8")).decode("ascii")


def _decode_people_data(payload: Optional[str]) -> Optional[List[Dict[str, str]]]:
    if not payload:
        return None
    try:
        raw = base64.b64decode(payload.encode("ascii"))
        return json.loads(raw.decode("utf-8"))
    except (binascii.Error, json.JSONDecodeError, UnicodeDecodeError) as exc:
        logger.warning("Failed to decode uploaded dataset: %s", exc)
        return None


def _build_locator(rows: Optional[List[Dict[str, str]]]) -> tuple[IdentityLocator, bool]:
    if rows:
        repo = PersonRepository(persons_from_dicts(rows))
        return IdentityLocator(repo), True
    repo = load_sample_repository()
    return IdentityLocator(repo), False


def _extract_search_params() -> Dict[str, Any]:
    params = {key: request.form.get(key, "").strip() for key in [
        "id_number",
        "first_name",
        "last_name",
        "street",
        "city",
        "house_number",
    ]}
    params["use_soundex"] = request.form.get("use_soundex") is not None
    return params


def _search(locator: IdentityLocator, params: Dict[str, Any]) -> List[MatchResult]:
    return locator.search(
        id_number=params.get("id_number") or None,
        first_name=params.get("first_name") or None,
        last_name=params.get("last_name") or None,
        street=params.get("street") or None,
        city=params.get("city") or None,
        house_number=params.get("house_number") or None,
        use_soundex=params.get("use_soundex", True),
    )


@app.route("/", methods=["GET", "POST"])
def index() -> str:
    messages: List[Dict[str, str]] = []
    results: Optional[List[MatchResult]] = None

    if "clear" in request.args:
        return redirect(url_for("index"))

    people_data_payload = ""
    people_rows: Optional[List[Dict[str, str]]] = None
    search_params: Dict[str, Any] = {"use_soundex": True}

    if request.method == "POST":
        people_data_payload = request.form.get("people_data_payload", "")
        people_rows = _decode_people_data(people_data_payload)
        search_params = _extract_search_params()
        locator, using_uploaded = _build_locator(people_rows)

        if "upload" in request.form and request.files.get("csv_file") and request.files["csv_file"].filename:
            file = request.files["csv_file"]
            try:
                stream = io.StringIO(file.stream.read().decode("utf-8-sig"), newline="")
                reader = csv.DictReader(stream)
                rows = [dict(row) for row in reader]
                people_rows = rows
                people_data_payload = _encode_people_data(rows)
                locator, using_uploaded = _build_locator(rows)
                messages.append({"text": f"הקובץ '{file.filename}' נטען בהצלחה.", "type": "success"})
            except (UnicodeDecodeError, csv.Error):
                messages.append({"text": "טעינת הקובץ נכשלה. ודא שהקובץ בפורמט CSV ושהקידוד שלו UTF-8.", "type": "error"})
            except Exception:
                logger.exception("Error processing uploaded file")
                messages.append({"text": "אירעה שגיאה בעת ניסיון לעבד את הקובץ.", "type": "error"})
            results = None
        elif "reset_sample" in request.form:
            people_rows = None
            people_data_payload = ""
            locator, using_uploaded = _build_locator(None)
            messages.append({"text": "המערכת חזרה לקובץ הדוגמה.", "type": "success"})
            results = None
        else:
            if any(search_params.get(key) for key in [
                "id_number",
                "first_name",
                "last_name",
                "street",
                "city",
                "house_number",
            ]):
                try:
                    results = _search(locator, search_params)
                    if not results:
                        messages.append({"text": "לא נמצאו תוצאות עבור פרטי החיפוש שסיפקת.", "type": "info"})
                except Exception:
                    logger.exception("Search failed")
                    messages.append({"text": "אירעה שגיאה בעת ניסיון לבצע את החיפוש. נסה שוב מאוחר יותר.", "type": "error"})
            using_uploaded = bool(people_rows)
    else:
        locator, using_uploaded = _build_locator(None)

    current_data = locator.repository.all()

    try:
        return render_template(
            "index.html",
            messages=messages,
            results=results,
            search=search_params,
            current_data=current_data,
            using_uploaded=using_uploaded,
            people_data_payload=people_data_payload,
        )
    except TemplateNotFound:
        error_msg = f"שגיאת תבנית: הקובץ 'index.html' לא נמצא. ודא שקובץ התבנית קיים בתיקיית: {app.template_folder}"
        logger.error(error_msg)
        return f"<h1>{error_msg}</h1>", 500


if __name__ == "__main__":
    app.run(debug=True, port=5000, host="127.0.0.1")
