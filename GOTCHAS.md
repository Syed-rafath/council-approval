# Gotchas

Every weird error and its fix. Newest first. Agents: append when you solve
something non-obvious.

## 2026-11-20 — `host="127.0.0.1"` makes app invisible to LAN/other devices

Flask's default `host="127.0.0.1"` only accepts connections from the server itself.
Any other machine (Windows browser, phone) gets a connection refused.
Fix: `host="0.0.0.0"` — listens on all network interfaces.
Only use `0.0.0.0` for local/LAN dev; Gunicorn+Nginx handles this in production.

## 2026-11-19 — Windows uses `venv\Scripts\activate`, not `source venv/bin/activate`

Local Phase 0 is on Windows. `source venv/bin/activate` is Linux/macOS.
Use `venv\Scripts\activate` in cmd/PowerShell, or run
`venv\Scripts\python.exe app.py` without activating.

<!-- Example entry:
## 2024-XX-XX — cloudflared tunnel 502
Nginx was listening on IPv6 only. Fix: `listen 80;` not `listen [::]:80;` in site conf.
-->
