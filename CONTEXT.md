# CONTEXT — read before doing anything

You are working on **PhotoReview**, a self-hosted Flask photo culling app.
Owner is learning Python and building this with AI agents. Optimize for
clarity, small steps, and working code over cleverness.

## Current phase

<!-- Update this line every session -->
Phase 0 — hello-world Flask. Developing on Windows first; Ubuntu/Cloudflare later.

## What works

- Flask hello-world on Windows: `python app.py` then http://127.0.0.1:5000
- `venv/` + `requirements.txt` (Flask only)
- Mobile-first hello page in `templates/index.html`

## What's next

- Confirm hello page in a browser on this Windows machine
- Stay on Phase 0 until that is reliable (do not start upload/thumbs yet)
- Later: Ubuntu Server, Nginx, Gunicorn, Cloudflare Tunnel, public phone URL
- Tag `p0-done` only after the public URL works from a phone

## What does NOT work / known issues

- Windows Python is 3.10.11 (server target is 3.11+). Fine for local Flask.
- App binds to 127.0.0.1 only — other devices on the LAN cannot reach it yet.
- No Ubuntu server, Nginx, or Cloudflare Tunnel yet.

## Rules for agents

1. **Read `README.md` first**, then this file. Update both when done.
2. **Stay in current phase.** Don't jump ahead. If you think a later-phase
   change is needed, note it under "What's next" instead of building it.
3. **One concern per commit.** Small, readable diffs. Format:
   `<phase>: <what>` (e.g. `p1: add upload route`).
4. **Commit at end of every session**, even if code is broken. Write
   "What works" / "What's next" before ending.
5. **Never delete originals.** Files always move to `To_Delete/`; the owner
   deletes manually.
6. **Never commit secrets or user data.** `votes.db`, `uploads/`, `thumbnails/`,
   `venv/`, `logs/`, `.env` are gitignored.
7. **Mobile-first.** Any UI you write must be usable at 375px width.
8. **Thumbnails required.** Never serve raw originals in list/review views.
9. **Ask before adding dependencies.** Each new pip package is a maintenance
   cost on a 4GB machine. Prefer stdlib.
10. **Don't refactor outside the current task.** If you spot a problem, write
    it under "Known issues" and move on.

## Environment facts

- Dev machine: Windows 10, Python 3.10.11, this repo
- Production target (later): old PC, 4GB RAM, 512GB HDD, Ubuntu Server LTS
- Public access (later): Cloudflare Tunnel, no port forwarding
- DB: SQLite at `votes.db` (gitignored) — not created yet
- Python venv: `venv/` in repo root
- Deploy dir (later): `/srv/photoreview`

## Session end checklist (agents must do this)

- [ ] Code committed with phase-prefixed message
- [ ] `CONTEXT.md` "What works" / "What's next" updated
- [ ] Any new gotchas added to `GOTCHAS.md`
- [ ] If a phase milestone is hit, tag it: `git tag p<N>-done`
