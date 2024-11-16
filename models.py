from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    role = db.Column(db.String(100), unique=False, nullable=False)
    location = db.Column(db.String(100), unique=False, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    service_users = db.relationship('ServiceUser', back_populates='user')  # Add this line to define the reverse relationship

    def __repr__(self):
        return f"<User {self.name}>"

# Vehicle Model
class Vehicles(db.Model):
    __tablename__ = 'vehicles'

    id = db.Column(db.Integer, primary_key=True)
    make = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    registration = db.Column(db.String(20), unique=True, nullable=False)
    transmission = db.Column(db.String(20), nullable=False)
    fuel_type = db.Column(db.String(20), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    service_users = db.relationship('ServiceUser', back_populates='vehicle')  # Add this line to define the reverse relationship

    def __repr__(self):
        return f'<Vehicle {self.make} {self.model}>'

# Service Model
class Service(db.Model):
    __tablename__ = 'services'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    cost = db.Column(db.Float, nullable=False)

    service_users = db.relationship('ServiceUser', back_populates='service')  # Add this line to define the reverse relationship
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "cost": self.cost
        }

# ServiceUser Model
class ServiceUser(db.Model):
    __tablename__ = 'service_user'
    
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Define relationships
    service = db.relationship('Service', back_populates='service_users')
    user = db.relationship('User', back_populates='service_users')
    vehicle = db.relationship('Vehicles', back_populates='service_users')

    def __repr__(self):
        return f"<ServiceUser(service_id={self.service_id}, user_id={self.user_id}, vehicle_id={self.vehicle_id})>"
