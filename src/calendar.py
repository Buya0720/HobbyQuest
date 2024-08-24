from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class TimeSlot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # start_time