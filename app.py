from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager
from flask_cors import CORS 

from models import db
from auth import auth_bp
from cars import cars_bp
from services import service_bp, service_user_bp

# Initialize Flask app
app = Flask(__name__)

# Load configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'  # Using SQLite for simplicity
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'supersecretkey'  # Secret key for JWT token

CORS(app, origins=["http://localhost:5175"])
# Initialize database and JWT manager
db.init_app(app)
jwt = JWTManager(app)

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
