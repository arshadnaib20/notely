# Notely

A quiet, distraction-free note-taking app. Write in Markdown, see it render live, and file notes with `#tags`.

Live demo: https://arshadnaib20.github.io/notely/

The live demo is the same frontend running entirely in your browser (notes are saved in your browser's local storage). This repository contains the full-stack version: a Flask + SQLite backend with a JSON API.

## What it does

- Create, edit and delete notes — autosaves as you type
- Live Markdown preview on the right pane
- Search across titles and bodies
- Tag filtering — any `#tag` in a note is auto-collected into the sidebar
- Light and dark themes, remembered between visits
- Responsive: works on phone and desktop

## Built with

- **Backend:** Python, Flask, SQLite
- **Frontend:** vanilla HTML, CSS and JavaScript (no frameworks), Markdown rendered by marked.js
- The whole thing is intentionally small enough to read end to end.

## API

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/notes` | List notes (optional `?q=search`, `?tag=work`) |
| GET | `/api/notes/<id>` | Fetch one note |
| POST | `/api/notes` | Create a note |
| PUT | `/api/notes/<id>` | Update a note |
| DELETE | `/api/notes/<id>` | Delete a note |
| GET | `/api/tags` | All tags with counts |

## Run locally

```bash
pip install -r requirements.txt
python app.py
```

Then open http://localhost:5000. The database is created and seeded with two welcome notes on first run.
