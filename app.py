import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, g, jsonify, render_template, request

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "notely.db"

app = Flask(__name__)


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL DEFAULT '',
            body TEXT NOT NULL DEFAULT '',
            tags TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    cur = conn.execute("SELECT COUNT(*) AS c FROM notes")
    if cur.fetchone()[0] == 0:
        now = datetime.now(timezone.utc).isoformat()
        welcome = [
            (
                "Welcome to Notely",
                "# Welcome\n\nNotely is a minimal, distraction-free note.\n\n"
                "- Press **New note** to start writing\n"
                "- Type in **Markdown** and see the preview on the right\n"
                "- Use `#tags` anywhere in a note to file it\n\n"
                "This is a personal project built with Flask and SQLite.",
                "welcome",
            ),
            (
                "A few things to try",
                "## Try this\n\n1. Search in the box above the list\n"
                "2. Click a tag to filter notes\n"
                "3. Toggle the moon icon for dark mode\n\n"
                "Notes autosave as you type.",
                "tips",
            ),
        ]
        for title, body, tags in welcome:
            conn.execute(
                "INSERT INTO notes (title, body, tags, created_at, updated_at) VALUES (?,?,?,?,?)",
                (title, body, tags, now, now),
            )
    conn.commit()
    conn.close()


def row_to_dict(r):
    return {
        "id": r["id"],
        "title": r["title"],
        "body": r["body"],
        "tags": [t for t in (r["tags"] or "").split(",") if t],
        "created_at": r["created_at"],
        "updated_at": r["updated_at"],
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.get("/api/notes")
def list_notes():
    q = request.args.get("q", "").strip().lower()
    tag = request.args.get("tag", "").strip()
    sql = "SELECT * FROM notes"
    clauses, params = [], []
    if q:
        clauses.append("(lower(title) LIKE ? OR lower(body) LIKE ?)")
        params.extend([f"%{q}%", f"%{q}%"])
    if tag:
        clauses.append("(',' || tags || ',') LIKE ?")
        params.append(f"%,{tag},%")
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY updated_at DESC"
    rows = get_db().execute(sql, params).fetchall()
    return jsonify([row_to_dict(r) for r in rows])


@app.get("/api/notes/<int:note_id>")
def get_note(note_id):
    row = get_db().execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    if not row:
        return jsonify({"error": "not found"}), 404
    return jsonify(row_to_dict(row))


@app.post("/api/notes")
def create_note():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "Untitled").strip()
    body = data.get("body") or ""
    tags = ",".join(sorted({t.strip().lstrip("#") for t in re.findall(r"#(\w+)", body)}))
    now = datetime.now(timezone.utc).isoformat()
    cur = get_db().execute(
        "INSERT INTO notes (title, body, tags, created_at, updated_at) VALUES (?,?,?,?,?)",
        (title, body, tags, now, now),
    )
    get_db().commit()
    row = get_db().execute("SELECT * FROM notes WHERE id = ?", (cur.lastrowid,)).fetchone()
    return jsonify(row_to_dict(row)), 201


@app.put("/api/notes/<int:note_id>")
def update_note(note_id):
    data = request.get_json(silent=True) or {}
    db = get_db()
    row = db.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    if not row:
        return jsonify({"error": "not found"}), 404
    title = (data.get("title", row["title"]) or "").strip()
    body = data.get("body", row["body"])
    tags = ",".join(sorted({t.strip().lstrip("#") for t in re.findall(r"#(\w+)", body)}))
    now = datetime.now(timezone.utc).isoformat()
    db.execute(
        "UPDATE notes SET title=?, body=?, tags=?, updated_at=? WHERE id=?",
        (title, body, tags, now, note_id),
    )
    db.commit()
    row = db.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    return jsonify(row_to_dict(row))


@app.delete("/api/notes/<int:note_id>")
def delete_note(note_id):
    db = get_db()
    db.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    db.commit()
    return jsonify({"ok": True})


@app.get("/api/tags")
def all_tags():
    rows = get_db().execute("SELECT tags FROM notes WHERE tags != ''").fetchall()
    counts = {}
    for r in rows:
        for t in r["tags"].split(","):
            t = t.strip()
            if t:
                counts[t] = counts.get(t, 0) + 1
    return jsonify([{"name": k, "count": v} for k, v in sorted(counts.items())])


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
