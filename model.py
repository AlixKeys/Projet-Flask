from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class Email(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(120))  # Optionnel : adresse de l'expéditeur
    content = db.Column(db.Text, nullable=False)  # Le message
    prediction = db.Column(db.String(10), nullable=False)  # "SPAM" ou "NON-SPAM"
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
