"""
models.py — PawPulse database models
Every table in pawpulse.db is defined here as a Python class.
Flask-SQLAlchemy translates these classes into SQL automatically.
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# This single `db` object is shared across the whole app.
# It gets "attached" to your Flask app inside app.py via db.init_app(app).
db = SQLAlchemy()


# ─────────────────────────────────────────────────────────────
#  FEEDER
#  A person or NGO volunteer who regularly feeds a dog.
# ─────────────────────────────────────────────────────────────
class Feeder(db.Model):
    __tablename__ = "feeder"

    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(100), nullable=False)
    phone      = db.Column(db.String(20))
    email      = db.Column(db.String(120))
    area       = db.Column(db.String(100))
    is_ngo     = db.Column(db.Boolean, default=False)   # True if this feeder is an NGO
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # One feeder → many dogs
    # backref="feeder" means on any Dog object you can write dog.feeder
    dogs = db.relationship("Dog", backref="feeder", lazy=True)

    def __repr__(self):
        return f"<Feeder id={self.id} name={self.name!r}>"


# ─────────────────────────────────────────────────────────────
#  DOG
#  The core record. Every stray dog that gets registered.
# ─────────────────────────────────────────────────────────────
class Dog(db.Model):
    __tablename__ = "dog"

    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(100), nullable=False)
    breed       = db.Column(db.String(100), default="Indie")
    color       = db.Column(db.String(100))
    description = db.Column(db.Text)           # any extra notes about appearance

    # Where the dog lives / is usually found
    latitude    = db.Column(db.Float, nullable=False)
    longitude   = db.Column(db.Float, nullable=False)
    area        = db.Column(db.String(100))    # human-readable e.g. "Madhapur"

    # Photos & QR
    photo_url   = db.Column(db.String(300))    # path to uploaded photo
    qr_code_url = db.Column(db.String(300))    # path to generated QR PNG

    # Health
    is_vaccinated   = db.Column(db.Boolean, default=False)
    is_sterilised   = db.Column(db.Boolean, default=False)
    medical_notes   = db.Column(db.Text)

    # Who feeds this dog (foreign key → feeder.id)
    # nullable=True because a dog can be registered without a known feeder
    feeder_id   = db.Column(db.Integer, db.ForeignKey("feeder.id"), nullable=True)

    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # One dog → many medical records
    medical_records = db.relationship("MedicalRecord", backref="dog", lazy=True,
                                      cascade="all, delete-orphan")

    # One dog → many emergency reports
    emergencies     = db.relationship("EmergencyReport", backref="dog", lazy=True)

    def __repr__(self):
        return f"<Dog id={self.id} name={self.name!r} area={self.area!r}>"

    def to_dict(self):
        """
        Converts this Dog into a plain dictionary.
        Called by the /api/dogs route so Leaflet.js can place map markers.
        """
        return {
            "id":            self.id,
            "name":          self.name,
            "breed":         self.breed,
            "area":          self.area or "",
            "latitude":      self.latitude,
            "longitude":     self.longitude,
            "is_vaccinated": self.is_vaccinated,
            "photo_url":     self.photo_url or "",
            "profile_url":   f"/dogs/{self.id}",
        }


# ─────────────────────────────────────────────────────────────
#  MEDICAL RECORD
#  Each vet visit, vaccination, or treatment gets its own row.
#  Linked to one dog. One dog can have many records over time.
# ─────────────────────────────────────────────────────────────
class MedicalRecord(db.Model):
    __tablename__ = "medical_record"

    id          = db.Column(db.Integer, primary_key=True)

    # Foreign key — which dog this record belongs to
    dog_id      = db.Column(db.Integer, db.ForeignKey("dog.id"), nullable=False)

    record_type = db.Column(db.String(50))     # e.g. "Vaccination", "Surgery", "Checkup"
    description = db.Column(db.Text, nullable=False)
    vet_name    = db.Column(db.String(100))
    cost        = db.Column(db.Float)          # in ₹, for donation transparency
    receipt_url = db.Column(db.String(300))    # uploaded bill/receipt photo
    date        = db.Column(db.Date, default=datetime.utcnow)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<MedicalRecord id={self.id} dog_id={self.dog_id} type={self.record_type!r}>"


# ─────────────────────────────────────────────────────────────
#  EMERGENCY REPORT
#  Filed by any citizen who spots an injured/sick dog.
#  Status moves: open → assigned → resolved
# ─────────────────────────────────────────────────────────────
class EmergencyReport(db.Model):
    __tablename__ = "emergency_report"

    id             = db.Column(db.Integer, primary_key=True)
    description    = db.Column(db.Text, nullable=False)
    photo_url      = db.Column(db.String(300))

    # Where the dog was spotted
    latitude       = db.Column(db.Float)
    longitude      = db.Column(db.Float)
    location_text  = db.Column(db.String(200))  # e.g. "Near Madhapur Dominos"

    # Which dog (optional — reporter may not know)
    dog_id         = db.Column(db.Integer, db.ForeignKey("dog.id"), nullable=True)

    # Who reported it
    reporter_name  = db.Column(db.String(100))
    reporter_phone = db.Column(db.String(20))

    # Lifecycle: open → assigned → resolved
    status         = db.Column(db.String(20), default="open")
    assigned_to    = db.Column(db.String(100))  # NGO/feeder name who took the case
    resolved_at    = db.Column(db.DateTime)

    created_at     = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<EmergencyReport id={self.id} status={self.status!r}>"

    def to_dict(self):
        return {
            "id":            self.id,
            "description":   self.description,
            "location_text": self.location_text or "",
            "latitude":      self.latitude,
            "longitude":     self.longitude,
            "status":        self.status,
            "created_at":    self.created_at.strftime("%d %b %Y"),
        }
