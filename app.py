import os
import qrcode
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from werkzeug.utils import secure_filename
from config import Config
from models import db, Dog, Feeder, EmergencyReport

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]
    )


def save_uploaded_photo(file, folder_key="UPLOAD_FOLDER"):
    """Save an uploaded photo and return its URL path."""
    if not file or file.filename == "":
        return None
    if not allowed_file(file.filename):
        return None
    filename = secure_filename(file.filename)
    folder = app.config[folder_key]
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, filename)
    file.save(filepath)
    subfolder = "uploads" if folder_key == "UPLOAD_FOLDER" else "qr"
    return f"/static/{subfolder}/{filename}"


def generate_qr(dog_id, base_url=None):
    """Generate a QR code PNG for a dog profile and return its URL path."""
    if base_url is None:
        base_url = "http://localhost:5000"
    profile_url = f"{base_url}/dogs/{dog_id}"
    img = qrcode.make(profile_url)
    qr_folder = app.config["QR_FOLDER"]
    os.makedirs(qr_folder, exist_ok=True)
    filename = f"dog_{dog_id}.png"
    img.save(os.path.join(qr_folder, filename))
    return f"/static/qr/{filename}"


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    total_dogs = Dog.query.count()
    total_emergencies = EmergencyReport.query.filter_by(status="open").count()
    recent_dogs = Dog.query.order_by(Dog.created_at.desc()).limit(6).all()
    return render_template(
        "index.html",
        total_dogs=total_dogs,
        open_emergencies=total_emergencies,
        recent_dogs=recent_dogs,
    )


@app.route("/dogs/new", methods=["GET", "POST"])
def register_dog():
    feeders = Feeder.query.all()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Dog name is required.", "error")
            return render_template("register_dog.html", feeders=feeders)

        photo_url = None
        if "photo" in request.files:
            photo_url = save_uploaded_photo(request.files["photo"])

        dog = Dog(
            name=name,
            breed=request.form.get("breed", "Unknown"),
            color=request.form.get("color", ""),
            latitude=float(request.form.get("latitude", 17.3850)),
            longitude=float(request.form.get("longitude", 78.4867)),
            area=request.form.get("area", ""),
            is_vaccinated=request.form.get("is_vaccinated") == "on",
            medical_notes=request.form.get("medical_notes", ""),
            feeder_id=request.form.get("feeder_id") or None,
            photo_url=photo_url,
        )
        db.session.add(dog)
        db.session.commit()

        # Generate QR after we have the dog ID
        qr_url = generate_qr(dog.id)
        dog.qr_code_url = qr_url
        db.session.commit()

        flash(f"{dog.name} registered successfully!", "success")
        return redirect(url_for("dog_profile", dog_id=dog.id))

    return render_template("register_dog.html", feeders=feeders)


@app.route("/dogs/<int:dog_id>")
def dog_profile(dog_id):
    dog = Dog.query.get_or_404(dog_id)
    emergencies = EmergencyReport.query.filter_by(dog_id=dog_id).order_by(
        EmergencyReport.created_at.desc()
    ).all()
    return render_template("dog_profile.html", dog=dog, emergencies=emergencies)


@app.route("/map")
def map_view():
    return render_template("map.html")


@app.route("/api/dogs")
def api_dogs():
    """JSON endpoint consumed by Leaflet.js on the map page."""
    dogs = Dog.query.all()
    return jsonify([dog.to_dict() for dog in dogs])


@app.route("/api/emergencies")
def api_emergencies():
    """JSON endpoint for emergency markers on the map."""
    reports = EmergencyReport.query.filter_by(status="open").all()
    data = []
    for r in reports:
        if r.latitude and r.longitude:
            data.append({
                "id": r.id,
                "description": r.description,
                "location_text": r.location_text or "",
                "latitude": r.latitude,
                "longitude": r.longitude,
                "status": r.status,
            })
    return jsonify(data)


@app.route("/emergency", methods=["GET", "POST"])
def report_emergency():
    dogs = Dog.query.order_by(Dog.name).all()
    if request.method == "POST":
        photo_url = None
        if "photo" in request.files:
            photo_url = save_uploaded_photo(request.files["photo"])

        lat_raw = request.form.get("latitude", "").strip()
        lng_raw = request.form.get("longitude", "").strip()

        report = EmergencyReport(
            description=request.form.get("description", "").strip(),
            location_text=request.form.get("location_text", ""),
            latitude=float(lat_raw) if lat_raw else None,
            longitude=float(lng_raw) if lng_raw else None,
            dog_id=request.form.get("dog_id") or None,
            reporter_name=request.form.get("reporter_name", ""),
            reporter_phone=request.form.get("reporter_phone", ""),
            photo_url=photo_url,
            status="open",
        )
        db.session.add(report)
        db.session.commit()
        flash("Emergency reported! An NGO will be notified.", "success")
        return redirect(url_for("emergencies_list"))

    return render_template("emergency.html", dogs=dogs)


@app.route("/emergencies")
def emergencies_list():
    reports = EmergencyReport.query.order_by(EmergencyReport.created_at.desc()).all()
    return render_template("emergencies.html", reports=reports)


@app.route("/emergencies/<int:report_id>/resolve", methods=["POST"])
def resolve_emergency(report_id):
    report = EmergencyReport.query.get_or_404(report_id)
    report.status = "resolved"
    db.session.commit()
    flash("Emergency marked as resolved.", "success")
    return redirect(url_for("emergencies_list"))


# ─── Init ─────────────────────────────────────────────────────────────────────

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
