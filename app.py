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


ensure_folders()
db.init_db()


def allowed_extension(filename: str) -> bool:
    return Path(filename).suffix.lower() in config.ALLOWED_EXTENSIONS


@app.get("/")
def index():
    batches = db.list_batches()
    return render_template("index.html", batches=batches)


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


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
