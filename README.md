# PhotoReview

Self-hosted photo culling web app. Upload batches of photos from your phone,
share a link with friends, they vote (swipe/keep-delete), low-scored photos are
auto-moved to a `To_Delete/` folder on the server for final confirmation.

**Goal:** clean up ~100GB of photos with zero cloud storage costs.

## Stack

- Ubuntu Server LTS on home PC (4GB RAM, 512GB HDD — old hardware, be gentle)
- Python 3 + Flask
- Gunicorn (WSGI) + systemd (process supervision)
- Nginx (reverse proxy + static files)
- SQLite (single-file DB, zero setup)
- Pillow (thumbnail generation — mandatory, HDD is slow)
- Cloudflare Tunnel (`cloudflared`) for public HTTPS access
- Frontend: plain HTML/CSS/JS, mobile-first. React only if v1 demands it.

## Architecture

```
Friends' phones
      │ HTTPS
      ▼
Cloudflare Tunnel (cloudflared on server)
      ▼
Nginx (:80/:443 local)
      ▼
Gunicorn (unix socket or :8000)
      ▼
Flask app (app.py)
      ├── SQLite (votes.db)
      └── Disk folders (uploads/, thumbnails/, To_Delete/, Kept/)
```

## Folder layout (on server, /srv/photoreview/)

```
/srv/photoreview/
  app.py                 # Flask entrypoint
  requirements.txt
  votes.db               # SQLite (gitignored)
  uploads/               # original photos uploaded by owner
  thumbnails/            # generated thumbs (gitignored)
  To_Delete/             # low-scored photos, awaiting owner confirmation
  Kept/                  # high-scored photos
  templates/             # Jinja2 templates
  static/                # CSS/JS assets
  venv/                  # python venv (gitignored)
  logs/                  # app logs (gitignored)
```

## Database schema (SQLite)

```sql
CREATE TABLE batches (
    id INTEGER PRIMARY KEY,
    created_at TEXT NOT NULL,
    label TEXT
);

CREATE TABLE photos (
    id INTEGER PRIMARY KEY,
    batch_id INTEGER NOT NULL REFERENCES batches(id),
    filename TEXT NOT NULL,
    thumb_filename TEXT,
    status TEXT NOT NULL DEFAULT 'pending',  -- pending | kept | delete
    created_at TEXT NOT NULL
);

CREATE TABLE friends (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    token TEXT NOT NULL UNIQUE  -- per-friend access token in URL
);

CREATE TABLE votes (
    id INTEGER PRIMARY KEY,
    photo_id INTEGER NOT NULL REFERENCES photos(id),
    friend_id INTEGER NOT NULL REFERENCES friends(id),
    vote TEXT NOT NULL,          -- keep | delete
    created_at TEXT NOT NULL,
    UNIQUE(photo_id, friend_id)
);
```

## API / routes (v1)

| Method | Path | Purpose |
|--------|------|---------|
| GET  | `/` | Owner dashboard: list batches |
| POST | `/upload` | Upload one or more photos (owner) |
| GET  | `/batch/<id>` | View a batch (owner) |
| GET  | `/review/<token>` | Friend review UI (mobile) |
| POST | `/api/vote` | Record a vote {photo_id, vote, token} |
| GET  | `/batch/<id>/results` | Owner: see vote tallies |
| POST | `/batch/<id>/apply` | Run threshold logic, move files |

## Decision rule (v1)

A photo moves to `To_Delete/` if:

- **strict majority** of votes are `delete`, AND
- total votes ≥ `ceil(friends_count / 2)` (minimum quorum)

Kept if majority `keep`. Otherwise stays `pending` (manual review).
Thresholds live in `config.py` so they can be tuned without code changes.

## Local development (Windows first)

The app is being built on a Windows machine. Ubuntu + Cloudflare Tunnel come later.
Do not treat a local hello-world as `p0-done`; that tag is for a public phone URL.

1. Install Python 3 (3.10+ is fine on Windows).
2. In the repo root:
   ```
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   python app.py
   ```
3. Open http://127.0.0.1:5000 in a browser. You should see "hello".

## Setup (Ubuntu server, later)

1. Install Ubuntu Server LTS, enable OpenSSH during install.
2. `sudo apt update && sudo apt install -y python3 python3-venv python3-pip nginx git sqlite3`
3. `git clone <repo> /srv/photoreview && cd /srv/photoreview`
4. `python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt`
5. Configure Gunicorn systemd unit (see `deploy/photoreview.service`).
6. Configure Nginx site (see `deploy/nginx.conf`).
7. Install `cloudflared`, run `cloudflared tunnel login`, create tunnel, route to `localhost:80`.
8. `sudo systemctl enable --now photoreview nginx cloudflared`
9. Open the public URL from your phone. If it loads, Phase 0 is done.

## Build order (phases)

- **Phase 0** — Hello-world Flask. Local Windows first; Ubuntu + Cloudflare Tunnel later for a public phone URL.
- **Phase 1** — Upload + thumbnail + grid display.
- **Phase 2** — Per-friend tokens + vote UI + SQLite persistence.
- **Phase 3** — Threshold logic + `shutil.move()` to `To_Delete/` + results page.
- **Phase 4** — Polish: batch-best-photo, richer UI, React if needed.

**Do not start Phase N+1 until Phase N works end-to-end from a phone.**

## Git conventions

- Commit at the end of every work session, even if code is broken.
- Format: `<phase>: <what>` — e.g. `p1: upload form saves to disk`
- Never commit `venv/`, `votes.db`, `uploads/`, `thumbnails/`, `To_Delete/`, `Kept/`, `logs/`.
- Tag working milestones: `git tag p0-done`, `p1-done`, etc.

## Non-negotiables

1. **Thumbnails from day 1.** HDD can't serve full-size images to friends.
2. **Mobile-first CSS.** Friends will use phones, not desktops.
3. **No scope creep** until a real friend has used v1.
4. **Never delete original files directly.** Always move to `To_Delete/` first;
   owner confirms deletion manually.
