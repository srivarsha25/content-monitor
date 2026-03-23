# Content Monitoring & Flagging System

A Django REST Framework backend that ingests content, identifies keyword-based matches, generates flags, and supports a human review workflow with suppression rules.

---

## Tech Stack

- Python 3.10+
- Django 6.0.3
- Django REST Framework
- SQLite (default Django DB)

---

## Project Structure

```
content-monitor/
├── core/
│   ├── settings.py        # Django project settings
│   └── urls.py            # Root URL routing
├── monitor/
│   ├── templates/
│   │   ├── admin/
│   │   │   └── login.html     # Custom animated admin login
│   │   └── login_page.html    # Standalone frontend login page
│   ├── admin.py           # Custom admin panel configuration
│   ├── models.py          # Keyword, ContentItem, Flag models
│   ├── serializers.py     # DRF serializers
│   ├── services.py        # Business logic: scoring, scanning, suppression
│   ├── tests.py           # Automated tests (10 tests)
│   ├── views.py           # API views + login page view
│   └── urls.py            # App-level URL routing
├── mock_data.json          # Local mock content dataset
├── manage.py
└── README.md
```

---

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/your-username/content-monitor.git
cd content-monitor
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install django djangorestframework
```

### 4. Run migrations

```bash
python manage.py migrate
```

### 5. Create an admin user (for the admin panel)

```bash
python manage.py createsuperuser
```

### 6. Start the server

```bash
python manage.py runserver
```

The API will be available at `http://127.0.0.1:8000/`

---

## Pages

| URL | Description |
|-----|-------------|
| `http://127.0.0.1:8000/login/` | Animated frontend login page |
| `http://127.0.0.1:8000/admin/` | Custom animated Django admin panel |

---

## Content Source

This project uses a **local mock JSON dataset** (`mock_data.json`) instead of a public API. This was a deliberate choice to keep the project fully self-contained and runnable without any API keys. The dataset contains 5 sample content items from different mock sources (Blog A–E).

The `load_mock_data()` function in `services.py` can be swapped for a real API call (e.g. NewsAPI, RSS feed) with minimal changes — just replace the file read with an HTTP request and return the same list format.

---

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/keywords/` | Create a keyword |
| POST | `/scan/` | Trigger a scan against mock data |
| GET | `/flags/` | List all generated flags |
| PATCH | `/flags/{id}/` | Update review status of a flag |

---

## Sample Requests (PowerShell)

### Create keywords

```powershell
Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:8000/keywords/" -ContentType "application/json" -Body '{"name": "django"}'
Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:8000/keywords/" -ContentType "application/json" -Body '{"name": "python"}'
Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:8000/keywords/" -ContentType "application/json" -Body '{"name": "automation"}'
Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:8000/keywords/" -ContentType "application/json" -Body '{"name": "data pipeline"}'
```

### Trigger a scan

```powershell
Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:8000/scan/"
```

### List all flags

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/flags/"
```

### Mark a flag as irrelevant

```powershell
Invoke-RestMethod -Method PATCH -Uri "http://127.0.0.1:8000/flags/1/" -ContentType "application/json" -Body '{"status": "irrelevant"}'
```

### Mark a flag as relevant

```powershell
Invoke-RestMethod -Method PATCH -Uri "http://127.0.0.1:8000/flags/1/" -ContentType "application/json" -Body '{"status": "relevant"}'
```

### Verify suppression (run scan again after marking a flag irrelevant)

```powershell
Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:8000/scan/"
# flags_skipped_suppressed will be > 0
```

---

## Scoring Logic

Matching is deterministic and easy to verify:

| Match Type | Score |
|------------|-------|
| Exact keyword match in title | 100 |
| All words of keyword found in title | 90 |
| Partial keyword match in title (substring) | 70 |
| All words of keyword found in body | 50 |
| Keyword appears in body (substring) | 40 |
| No match | 0 (no flag created) |

Multi-word keywords like "data pipeline" are supported — if both words appear in the title, the flag scores 90 instead of a basic substring match.

---

## Suppression Logic

This is the core business rule of the system.

**Rule:** If a flag has been marked `irrelevant`, it will not be re-created on subsequent scans unless the underlying `ContentItem` has changed.

**Implementation:**
- When a flag is created, the `content_snapshot` field stores the `last_updated` timestamp of the content item at the time of flagging.
- On each scan, if a flag already exists with `status = irrelevant`, the system compares the content item's current `last_updated` against the stored `content_snapshot`.
- If `last_updated > content_snapshot` — content has changed — the flag is reset to `pending` and re-surfaced for review.
- If `last_updated == content_snapshot` — content has not changed — the flag is skipped (suppressed).

**Assumption:** `ContentItem` uniqueness is determined by `(title, source)`. If the same title appears from the same source with a newer `last_updated`, it is treated as updated content.

---

## Deduplication

The `Flag` model enforces a `unique_together` constraint on `(keyword, content_item)`. This prevents duplicate flags from being created on repeated scans for the same keyword-content pair. If a flag already exists and the content hasn't changed, the score is updated but no new flag is created.

---

## Running Tests

```bash
python manage.py test monitor
```

10 automated tests covering:
- Scoring logic (exact, partial, body, multi-word matches)
- Suppression behavior (flags stay irrelevant when content unchanged)
- Content change detection (flags reset to pending when content updates)
- Deduplication (no duplicate flags on repeated scans)

Expected output:
```
Ran 10 tests in 0.XXXs
OK
```

---

## Bonus Features Implemented

- **Deduplication** — `unique_together` constraint on Flag model prevents duplicate flags
- **Improved matching logic** — multi-word keyword support with granular scoring tiers
- **Admin improvements** — custom admin panel with searchable, filterable, inline-editable flag list
- **Animated login pages** — custom admin login and standalone `/login/` frontend page with animated background, floating particles, and glowing effects
- **Automated tests** — 10 tests covering all critical business logic paths

---

## Design Decisions & Trade-offs

- **Service layer separation:** All business logic (scanning, scoring, suppression) lives in `services.py`, keeping views thin and easy to test independently.
- **Mock data over public API:** Chosen for simplicity and self-contained setup. The `load_mock_data()` function in `services.py` can be swapped for a real API call with minimal changes.
- **SQLite:** Sufficient for this scope. Can be replaced with PostgreSQL by updating `DATABASES` in `settings.py`.
- **No authentication on API endpoints:** Not in scope for this assignment. In production, API endpoints would require token or session authentication.
- **`content_snapshot` field on Flag:** This is the key to suppression — it records the `last_updated` timestamp of the content at the time the flag was last evaluated, enabling reliable change detection without storing full content diffs.
- **Celery not implemented:** Background processing with Celery was listed as optional. Given the scan is fast and synchronous for this dataset size, a simple API-triggered scan is cleaner and easier to reason about for this scope.
