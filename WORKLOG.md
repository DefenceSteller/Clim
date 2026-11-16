# Worklog

## 2026-11-16

### Chatbot UI styling
- Restyled `templates/climatechanges/chatbot.html` to match the website theme.
- Replaced plain white chat box with themed layout:
  - Site breadcrumb/section header integration
  - Gradient chat header and branded message bubbles
  - Styled input/send button and improved spacing/responsiveness
  - Dark-theme compatible styling tweaks
- Preserved chatbot functionality (`/chatbot/api/` fetch, CSRF handling, message rendering flow).

### Sticky navbar fix
- Investigated header overlap/cutoff issue on scroll.
- Updated `static/css/style.css` sticky header rules across breakpoints:
  - Forced sticky header to `top: 0` with fixed positioning/z-index
  - Disabled sticky animation/transform offsets causing cut-off
  - Hid top header bar while sticky to prevent layout jump
- Updated `static/js/main.js` sticky toggle to reset/apply inline positioning styles for consistent behavior.

### Support pages UI styling
- Restyled support templates to match site theme (layout, cards, forms, buttons, tables, conversation UI):
  - `templates/climatechanges/support.html` (request submission form)
  - `templates/climatechanges/my_tickets.html` (tickets table/list with status badges)
  - `templates/climatechanges/ticket_detail.html` (ticket info, conversation thread, reply form)
- Kept backend behavior and form/URL/CSRF logic unchanged.

### Documentation
- Added `README.md` with project overview, features, routes, setup, and notes.
- Added `WORKLOG.md` and `PROGRESS.md` to track changes and status.
