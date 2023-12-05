from extensions import db
from flask_login import UserMixin

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(500), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    projects = db.relationship('Project', backref='user', lazy=True)        
