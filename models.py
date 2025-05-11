from datetime import datetime
from app import db
from flask_login import UserMixin


from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_hall_incharge = db.Column(db.Boolean, default=False)
    managed_halls = db.relationship('Hall', backref='incharge', lazy='dynamic')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with bookings
    bookings = db.relationship('Booking', foreign_keys='Booking.user_id', backref='user', lazy='dynamic')
    
    def __repr__(self):
        return f'<User {self.username}>'
        
    def get_id(self):
        return str(self.id)
    
    # Relationship with bookings (specify foreign_keys to avoid ambiguity)
    bookings = db.relationship('Booking', foreign_keys='Booking.user_id', backref='user', lazy='dynamic')
    
    def __repr__(self):
        return f"<User {self.username}>"


class Hall(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    hall_type = db.Column(db.String(20), nullable=False)  # 'seminar' or 'computer'
    capacity = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)
    features = db.Column(db.Text)
    image_url = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    incharge_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relationship with bookings
    bookings = db.relationship('Booking', backref='hall', lazy='dynamic')
    
    def __repr__(self):
        return f"<Hall {self.name}>"


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    hall_id = db.Column(db.Integer, db.ForeignKey('hall.id'), nullable=False)
    event_name = db.Column(db.String(100), nullable=False)
    event_description = db.Column(db.Text)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    attendees = db.Column(db.Integer)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relationship with administrator who approved/rejected
    admin = db.relationship('User', foreign_keys=[approved_by], backref='approved_bookings')
    
    def __repr__(self):
        return f"<Booking {self.event_name}>"
    
    @property
    def duration_hours(self):
        """Calculate the duration of the booking in hours"""
        duration = self.end_time - self.start_time
        return duration.total_seconds() / 3600
