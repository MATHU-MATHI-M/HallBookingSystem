import os
import logging

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy with the Base
db = SQLAlchemy(model_class=Base)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///college_booking.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize SQLAlchemy with the app
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Create database tables
with app.app_context():
    import models  # noqa: F401
    db.drop_all()  # Reset the database
    db.create_all()  # Create new tables with correct schema
    
    from models import User, Hall
    def create_demo_halls():
        for i in range(1, 11):
            seminar_hall = Hall(
                name=f'Seminar Hall {i}',
                hall_type='seminar',
                capacity=50,  # Default capacity for seminar halls
                description=f'A spacious seminar hall suitable for presentations and lectures',
                features='Projector, Audio System, Whiteboard'
            )
            db.session.add(seminar_hall)
            cc_hall = Hall(
                name=f'CC Hall {i}',
                hall_type='cc',
                capacity=30,  # Default capacity for computer centers
                description=f'Fully equipped computer center for practical sessions',
                features='Computers, Internet, Development Software'
            )
            db.session.add(cc_hall)
        db.session.commit()
        logging.info("Demo halls created")

    # Create demo halls
    create_demo_halls()

    # Create admin and default user if they don't exist
    admin = User.query.filter_by(username='admin').first()
    default_user = User.query.filter_by(username='user').first()

    if not admin:
        from werkzeug.security import generate_password_hash
        admin = User(
            username='admin',
            email='admin@college.edu',
            password_hash=generate_password_hash('adminpassword'),
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
        logging.info("Admin user created")

    if not default_user:
        from werkzeug.security import generate_password_hash
        user = User(
            username='user',
            email='user@college.edu',
            password_hash=generate_password_hash('userpassword'),
            is_admin=False
        )
        db.session.add(user)
        db.session.commit()
        logging.info("Default user created")

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Import and register routes
from routes import *  # noqa: F401, F403

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)