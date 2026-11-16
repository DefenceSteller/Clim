# Project Progress

Status legend: **Done** | **In Progress** | **Planned** | **Needs Review**

## Core Pages & Layout
- [x] **Done** – Base site template and theme asset integration (`template.html`, static CSS/JS)
- [x] **Done** – Home/About/Contact templates and routes
- [x] **Done** – Sticky navbar scroll behavior fix (cutoff/offset issue addressed)

## Authentication & User Profile
- [x] **Done** – Signup flow creates Django `User` and `Customer` profile
- [x] **Done** – Login/logout-capable auth wiring (`login_view` implemented)
- [ ] **Needs Review** – Password handling consistency/security (`Customer.password` stored separately; auth uses Django user) and overall auth hardening

## Prediction Modules
- [x] **Done** – Temperature prediction page/route/view present
- [x] **Done** – Disaster prediction page/route/view present
- [x] **Done** – Carbon prediction page/route/view present
- [ ] **Needs Review** – Model/data dependencies, validation, and runtime requirements for prediction features

## Chatbot
- [x] **Done** – Chatbot UI page and JSON API endpoint
- [x] **Done** – Dataset-backed temperature query flow (`media/Temperature.xls`)
- [x] **Done** – UI restyled to match website theme
- [ ] **Needs Review** – API key management (currently hardcoded), error handling, and response formatting/security

## Support System
- [x] **Done** – Support ticket models/forms/admin integration
- [x] **Done** – Submit support request, list my tickets, ticket detail/reply views
- [x] **Done** – Support pages restyled to match website theme
- [ ] **Planned** – Ticket status updates by staff workflow/UI (if required beyond admin)
- [ ] **Planned** – Attachments/notifications (if needed)

## Project Setup & Documentation
- [x] **Done** – `README.md`, `WORKLOG.md`, `PROGRESS.md` added
- [ ] **Planned** – Add `requirements.txt` / dependency lock and environment variable configuration docs (`.env` example)
- [ ] **Planned** – Add automated tests for key flows (auth, support, chatbot API)

## Deployment/Quality (Recommended Next)
- [ ] **Planned** – Move secrets to environment variables and rotate exposed keys
- [ ] **Planned** – Production settings hardening (`DEBUG`, `ALLOWED_HOSTS`, static/media serving, secret key)
- [ ] **Planned** – Code cleanup/refactor (duplicate imports, large `views.py`, app/project structure consistency)
