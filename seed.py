"""
Run once to populate the database with demo data.
Usage: python seed.py
"""
from app import app
from models import db, Dog, Feeder, EmergencyReport

FEEDERS = [
    {"name": "Anjali Reddy",   "phone": "9876543210", "area": "Banjara Hills"},
    {"name": "Suresh Kumar",   "phone": "9845123456", "area": "Madhapur"},
    {"name": "Priya Sharma",   "phone": "9765432198", "area": "Kondapur"},
    {"name": "Animal Aid NGO", "phone": "9988776655", "area": "Gachibowli"},
]

# (name, breed, color, lat, lng, area, vaccinated, notes)
DOGS = [
    ("Bruno",    "Indie",          "Brown",        17.4156, 78.4347, "Banjara Hills",  True,  "Friendly, sterilised"),
    ("Moti",     "Indie",          "White",        17.4500, 78.3800, "Jubilee Hills",  True,  "Limps slightly, monitored"),
    ("Kalu",     "Indie",          "Black",        17.4123, 78.4678, "Madhapur",       False, "Very shy, leave food and step back"),
    ("Rani",     "Indie mix",      "Brown-white",  17.4402, 78.3947, "Kondapur",       True,  "Nursing pups nearby"),
    ("Tiger",    "Indie",          "Tan",          17.3850, 78.4867, "Gachibowli",     True,  "Playful, knows sit command"),
    ("Bholi",    "Labrador mix",   "Yellow",       17.4900, 78.3600, "Begumpet",       True,  "Very gentle, good with kids"),
    ("Rocky",    "Indie",          "Grey",         17.3600, 78.4750, "Tolichowki",     False, "Needs rabies booster in Dec"),
    ("Simba",    "Indie",          "Brown",        17.4300, 78.4800, "HITEC City",     True,  "Guard dog for the park"),
    ("Laxmi",    "Indie",          "Black-white",  17.4050, 78.4600, "Kukatpally",     False, "Pregnant, due soon"),
    ("Charlie",  "Indie mix",      "Tan",          17.4700, 78.4200, "Secunderabad",   True,  "Old dog, about 10 yrs"),
    ("Pinki",    "Spitz mix",      "White",        17.4250, 78.4550, "Ameerpet",       True,  "Lost eye in accident, adapted well"),
    ("Koda",     "Indie",          "Brown",        17.3950, 78.4700, "Nanakramguda",   True,  "Loves mango season"),
    ("Sheru",    "Indie",          "Brown-black",  17.4600, 78.4900, "Malkajgiri",     False, "Aggressive around food, approach calmly"),
    ("Golu",     "Indie",          "White",        17.4150, 78.4200, "Film Nagar",     True,  "Comes to the same spot every 6pm"),
    ("Roja",     "Indie mix",      "Red-brown",    17.3750, 78.5100, "LB Nagar",       True,  "Recovered from mange, doing great"),
    ("Hero",     "Indie",          "Black",        17.4800, 78.5000, "Uppal",          False, "Injured back paw, healing"),
    ("Nandu",    "Indie",          "Brown",        17.4000, 78.3900, "Manikonda",      True,  "Feeds from Patel family daily"),
    ("Diya",     "Indie",          "Cream",        17.4350, 78.4700, "Madhapur",       True,  "Follows school kids every morning"),
    ("Kiran",    "Indie mix",      "Grey-white",   17.4550, 78.4400, "Borabanda",      False, "Needs deworming"),
    ("Bunty",    "Indie",          "Tan",          17.3700, 78.4900, "Attapur",        True,  "Local favourite at chai stall"),
]

EMERGENCIES = [
    {
        "description": "Dog hit by bike near signal, limping badly",
        "location_text": "Madhapur main road near Dominos",
        "latitude": 17.4502,
        "longitude": 78.3912,
        "reporter_name": "Ravi Teja",
        "status": "open",
    },
    {
        "description": "Stray with large wound on neck, needs urgent vet",
        "location_text": "Kondapur petrol bunk opposite",
        "latitude": 17.4430,
        "longitude": 78.3860,
        "reporter_name": "Sita Devi",
        "status": "open",
    },
    {
        "description": "Dog trapped in drain near park",
        "location_text": "Gachibowli stadium road",
        "latitude": 17.3880,
        "longitude": 78.3910,
        "reporter_name": "Anonymous",
        "status": "resolved",
    },
]


def seed():
    with app.app_context():
        # Clear existing data
        EmergencyReport.query.delete()
        Dog.query.delete()
        Feeder.query.delete()
        db.session.commit()

        # Create feeders
        feeder_objects = []
        for f in FEEDERS:
            feeder = Feeder(**f)
            db.session.add(feeder)
            feeder_objects.append(feeder)
        db.session.commit()

        # Create dogs
        for i, (name, breed, color, lat, lng, area, vacc, notes) in enumerate(DOGS):
            feeder = feeder_objects[i % len(feeder_objects)]
            dog = Dog(
                name=name,
                breed=breed,
                color=color,
                latitude=lat,
                longitude=lng,
                area=area,
                is_vaccinated=vacc,
                medical_notes=notes,
                feeder_id=feeder.id,
            )
            db.session.add(dog)
        db.session.commit()

        # Generate QR codes for all dogs
        from app import generate_qr
        for dog in Dog.query.all():
            dog.qr_code_url = generate_qr(dog.id)
        db.session.commit()

        # Create emergency reports
        dogs = Dog.query.all()
        for i, e in enumerate(EMERGENCIES):
            report = EmergencyReport(
                dog_id=dogs[i].id if i < len(dogs) else None,
                **e,
            )
            db.session.add(report)
        db.session.commit()

        print(f"Seeded {Dog.query.count()} dogs, "
              f"{Feeder.query.count()} feeders, "
              f"{EmergencyReport.query.count()} emergency reports.")
        print("Done! Run: flask run")


if __name__ == "__main__":
    seed()
