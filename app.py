import math
import secrets
import shutil
import uuid
from pathlib import Path

from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
import config
import db
from thumbs import UnidentifiedImageError, make_thumbnail

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_LENGTH
app.secret_key = config.SECRET_KEY


def ensure_folders():
    config.UPLOAD_DIR.mkdir(exist_ok=True)
    config.THUMB_DIR.mkdir(exist_ok=True)
    config.TO_DELETE_DIR.mkdir(exist_ok=True)
    config.KEPT_DIR.mkdir(exist_ok=True)


ensure_folders()
db.init_db()


def allowed_extension(filename: str) -> bool:
    return Path(filename).suffix.lower() in config.ALLOWED_EXTENSIONS


@app.get("/")
def index():
    batches = db.list_batches()
    friends = db.list_friends()
    return render_template("index.html", batches=batches, friends=friends)


@app.post("/friends/add")
def add_friend():
    name = (request.form.get("name") or "").strip()
    if not name:
        flash("Name is required.")
        return redirect(url_for("index"))
    token = secrets.token_urlsafe(16)
    db.create_friend(name, token)
    flash(f"Added {name}. Share their review link below.")
    return redirect(url_for("index"))


@app.post("/upload")
def upload():
    files = request.files.getlist("photos")
    label = (request.form.get("label") or "").strip() or None
    saved = 0
    skipped = 0
    batch_id = None

    for file in files:
        if not file or not file.filename:
            continue
        if not allowed_extension(file.filename):
            skipped += 1
            continue

        ext = Path(file.filename).suffix.lower()
        stored_name = f"{uuid.uuid4().hex}{ext}"
        dest = config.UPLOAD_DIR / stored_name
        file.save(dest)

        thumb_name = f"{Path(stored_name).stem}.jpg"
        try:
            make_thumbnail(dest, thumb_name)
        except (UnidentifiedImageError, OSError):
            dest.unlink(missing_ok=True)
            skipped += 1
            continue

        if batch_id is None:
            batch_id = db.create_batch(label)
        db.add_photo(batch_id, stored_name, thumb_name)
        saved += 1

    if saved == 0:
        flash("No photos were saved. Use jpg, png, webp, or gif.")
        return redirect(url_for("index"))

    if skipped:
        flash(f"Saved {saved} photo(s). Skipped {skipped} file(s).")
    else:
        flash(f"Saved {saved} photo(s).")
    return redirect(url_for("batch_view", batch_id=batch_id))


@app.get("/batch/<int:batch_id>")
def batch_view(batch_id):
    batch = db.get_batch(batch_id)
    if batch is None:
        abort(404)
    photos = db.list_photos(batch_id)
    return render_template("batch.html", batch=batch, photos=photos)


@app.get("/thumbs/<path:filename>")
def thumbnail(filename):
    # Grid views only. Originals stay on disk and are never served here.
    return send_from_directory(config.THUMB_DIR, filename)


@app.get("/review/<token>")
def review(token):
    friend = db.get_friend_by_token(token)
    if friend is None:
        abort(404)
    photo = db.get_next_unvoted(friend["id"])
    remaining = db.count_unvoted(friend["id"])
    return render_template("review.html", friend=friend, photo=photo, remaining=remaining)


@app.post("/review/<token>/vote")
def cast_vote(token):
    friend = db.get_friend_by_token(token)
    if friend is None:
        abort(404)
    photo_id = request.form.get("photo_id", type=int)
    vote = request.form.get("vote")
    if vote not in ("keep", "delete") or not photo_id:
        abort(400)
    db.record_vote(photo_id, friend["id"], vote)
    return redirect(url_for("review", token=token))


@app.get("/batch/<int:batch_id>/results")
def batch_results(batch_id):
    batch = db.get_batch(batch_id)
    if batch is None:
        abort(404)
    photos = db.get_vote_tallies(batch_id)
    friends_count = db.count_friends()
    quorum = math.ceil(friends_count * config.QUORUM) if friends_count > 0 else 1
    return render_template(
        "results.html",
        batch=batch,
        photos=photos,
        friends_count=friends_count,
        quorum=quorum,
    )


@app.post("/batch/<int:batch_id>/apply")
def batch_apply(batch_id):
    batch = db.get_batch(batch_id)
    if batch is None:
        abort(404)

    photos = db.get_vote_tallies(batch_id)
    friends_count = db.count_friends()
    quorum = math.ceil(friends_count * config.QUORUM) if friends_count > 0 else 1

    moved_delete = 0
    moved_kept = 0
    skipped = 0

    for photo in photos:
        if photo["status"] != "pending":
            continue  # already decided in a previous apply

        if photo["total_votes"] < quorum:
            skipped += 1
            continue  # not enough votes yet

        src = config.UPLOAD_DIR / photo["filename"]

        if photo["delete_count"] > photo["keep_count"]:
            dest = config.TO_DELETE_DIR / photo["filename"]
            if src.exists():
                shutil.move(str(src), str(dest))
            db.update_photo_status(photo["id"], "delete")
            moved_delete += 1
        else:
            dest = config.KEPT_DIR / photo["filename"]
            if src.exists():
                shutil.move(str(src), str(dest))
            db.update_photo_status(photo["id"], "kept")
            moved_kept += 1

    parts = []
    if moved_delete:
        parts.append(f"{moved_delete} → To_Delete/")
    if moved_kept:
        parts.append(f"{moved_kept} → Kept/")
    if skipped:
        parts.append(f"{skipped} still pending (below quorum of {quorum} vote(s))")
    flash(", ".join(parts) if parts else "Nothing to apply.")
    return redirect(url_for("batch_results", batch_id=batch_id))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
