?# Id Locator

������ ������ ���� ����� ���� �� ����� ��� ����� ����� ����� ����, �� ����� ��������� Soundex ������ ������ ���� ����� ��������.

## ������ �������
- ����� ��� �� ������ ����� CSV �� ������ ����� ����.
- ����� ��� ����� ����, ����� �� �� ���.
- ������ Soundex ����� ������ ������ ������ ����� ������� �� ������ ���� ������.
- ���� CLI ����� ����� ������� ������� ����� ������.
- ��� UI ����� Flask ������ ����� ������ ������ ����� �����, ���� ������ ������ ����� ���� ��� ����� �� 20 ������ ������.

## ����� ������
1. ���� ��� ��� Python 3.10 ����� �����.
2. ������ �� ������� �������:
   ```bash
   pip install .
   ```
3. ����� �-CLI:
   ```bash
   python -m idlocator.cli --help
   ```
4. ����� ��� �-UI:
   ```bash
   python -m idlocator.web.app
   ```
   ���� ���� ������ http://127.0.0.1:5000/ (���� ����� �����).

   �� ���� 5000 ����, ���� ����� �� ���� �� ���� ��� ������� ������:
   ```bash
   python -m idlocator.web.app --port 8080
   ```
   ����� ��, ���� ���� ���� ������ http://127.0.0.1:8080/.

   ���� ����� ����� ��� ������ �����:
   - "����� ���� ����� ���" (������ ������ �����)
   - "����� ���� ����� (20 ������ ������)"
   ���� ���� �� ������ ���� ������� ���� ����� ��� ���� ������.

## ���� ������ ������
- `data/sample_people.csv` � ���� ����� �� ���� ������.
- `data/sample_people_20.csv` � �� ������ ���� ���� �� 20 ������ ������ ����� ����� �������.
- `data/people_template.csv` � ����� ���� ������.

## ������
- ���� ������ ����� (������):
  ```bash
  python -m unittest tests.test_service
  ```
- ���� ������ ���� CLI (���� UI):
  ```bash
  python -m unittest tests.ui.test_cli_ui
  ```

## ���� �������
```
idlocator/
??? __init__.py
??? cli.py
??? models.py
??? repository.py 
??? service.py
??? soundex.py
??? web/
    ??? __init__.py
    ??? app.py
    ??? templates/
        ??? index.html  <-- ���� �-HTML �� ����
data/
??? people_template.csv
??? sample_people.csv
??? sample_people_20.csv
tests/
??? __init__.py
??? test_service.py
??? ui/
    ??? __init__.py
    ??? test_cli_ui.py
pyproject.toml
README.md
```

## ������� ������
- ��������� ���� ������ ����� ����� ���� CSV.
- ����� ����������� ������ ������ ������� (���� Levenshtein �� fuzzywuzzy).
- ����� REST API ������� FastAPI �� Flask.

## Deploying to Google Cloud Run
To serve the Flask UI on the public internet you can deploy the app to Cloud Run and let Firebase Hosting proxy traffic to it.

1. Install the Google Cloud SDK and authenticate:
   ```bash
   gcloud auth login
   gcloud config set project idlocator-627e0
   ```
2. Build and push the container image using the Dockerfile in the project root:
   ```bash
   gcloud builds submit --tag gcr.io/idlocator-627e0/idlocator-web
   ```
3. Deploy the service to Cloud Run (choose the same region you will reference from Firebase, for example `us-central1`):
   ```bash
   gcloud run deploy idlocator-web \
     --image gcr.io/idlocator-627e0/idlocator-web \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated
   ```
4. After the service is live, redeploy Firebase Hosting so `firebase.json` routes all traffic to Cloud Run:
   ```bash
   firebase deploy --only hosting
   ```
5. Visit either the Cloud Run URL that is returned by step 3 or the Firebase Hosting URL (`https://idlocator-627e0.web.app`) to use the UI.


