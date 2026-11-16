# Climate Changes Web App

A Django-based web application for climate awareness and analysis, including temperature/disaster/carbon prediction pages, an AI chatbot for temperature queries, user authentication, and a support ticket system.

## Features

- **Public pages:** Home, About, Contact
- **User auth:** Signup, Login (custom `Customer` profile linked to Django `User`)
- **AI/Prediction modules:**
  - Temperature prediction (`/climatechanges/climateTempPrediction/`)
  - Disaster prediction (`/climatechanges/climateDisasterPrediction/`)
  - Carbon prediction (`/climatechanges/carbon-prediction/`)
- **Climate chatbot:** Chat UI with API endpoint backed by dataset lookup + Gemini response generation (`media/Temperature.xls`)
- **Support center (login required):**
  - Submit support/feedback request
  - View my requests
  - Ticket detail and conversation/messages
- **Admin:** Django admin for users/models and support ticket management

## Tech Stack

- Python + Django
- SQLite (`db.sqlite3`)
- HTML templates (Django templating), Bootstrap/theme CSS/JS assets
- pandas (dataset handling in prediction/chatbot features)
- Google GenAI client (`google.genai`) for chatbot responses

## Project Structure (key paths)

- `manage.py` – Django management entry point
- `mysite/` – project settings and root URL config
- `urls.py`, `views.py`, `models.py`, `forms.py`, `admin.py` – app logic (current layout)
- `templates/climatechanges/` – page templates
- `static/` – CSS/JS/fonts/images
- `media/` – datasets and uploaded/media assets
- `migrations/` – database migrations

## Routes

Root URL config mounts app at:
- `/climatechanges/` (includes app routes)
- `/admin/`

Main app routes (under `/climatechanges/`):
- `/`, `/index/` – Home
- `/about/` – About
- `/contact/` – Contact
- `/login/`, `/signup/` – Auth
- `/climateTempPrediction/` – Temperature prediction
- `/climateDisasterPrediction/` – Disaster prediction
- `/carbon-prediction/` – Carbon prediction
- `/chatbot/` – Chatbot UI
- `/chatbot/api/` – Chatbot JSON API
- `/support/` – Create support request (login required)
- `/my-tickets/` – List user tickets (login required)
- `/ticket/<id>/` – Ticket detail/messages (login required)

## Setup & Run

1. **Create/activate a Python environment** (recommended).
2. **Install dependencies** (no `requirements.txt` currently in repo; install based on usage):
   ```bash
   pip install django pandas google-genai openpyxl xlrd
   ```
   > Additional packages may be required depending on your local environment and prediction implementations.
3. **Apply migrations:**
   ```bash
   python manage.py migrate
   ```
4. **(Optional) Create superuser:**
   ```bash
   python manage.py createsuperuser
   ```
5. **Run development server:**
   ```bash
   python manage.py runserver
   ```
6. Open: `http://127.0.0.1:8000/climatechanges/`

## Data & Configuration Notes

- Chatbot expects `media/Temperature.xls` (sheet: `Indicator_3_1_Climate_Indicator`).
- Static/media configuration should be verified for your deployment setup.
- `views.py` currently contains a hardcoded Gemini API key; move secrets to environment variables before sharing/deploying.
- `DEBUG=True` and default secret key settings are development-oriented; review `mysite/settings.py` for production hardening.

## UI Notes

- Site uses a shared base template (`templates/climatechanges/template.html`) and theme assets in `static/`.
- Chatbot and support pages have been restyled to align with the site theme (cards, breadcrumb/headers, themed inputs/buttons/messages).
