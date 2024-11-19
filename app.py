from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager
from flask_cors import CORS 
from datetime import timedelta

from models import db
from auth import auth_bp
from cars import cars_bp
from services import service_bp, service_user_bp
from flask_mail import Mail, Message as MailMessage

# Initialize Flask app
app = Flask(__name__)

# Load configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'  # Using SQLite for simplicity
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'supersecretkey'  # Secret key for JWT token
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=3600)

app.config['MAIL_SERVER'] = "smtp.gmail.com"
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = "benson.gacheru@student.moringaschool.com"
app.config['MAIL_PASSWORD'] = "omsozwirnhszhvan"
app.config['MAIL_DEFAULT_SENDER'] = "benson.gacheru@student.moringaschool.com"

CORS(app, origins=["http://localhost:5173", "https://okoa-gari-client.vercel.app"])
# Initialize database and JWT manager
db.init_app(app)
jwt = JWTManager(app)
mail = Mail(app)

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(cars_bp, url_prefix='/cars')
app.register_blueprint(service_bp, url_prefix='/services')
app.register_blueprint(service_user_bp, url_prefix='/service_user')

# Home route to test app
@app.route('/')
def home():
    return jsonify({"msg": "Welcome to the Flask app!"}), 200

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # This creates the tables in the database
    app.run(debug=True)
