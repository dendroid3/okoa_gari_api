from flask import Blueprint, request, jsonify, make_response
from models import db, User
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash

# Create a blueprint for authentication routes
auth_bp = Blueprint('auth', __name__)

# Register User
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    # Validate input
    if not data.get('name') or not data.get('email') or not data.get('password') or not data.get('location') or not data.get('role'):
        return make_response({"msg": "Missing fields"}, 400)

    # Check if user already exists
    user_exists = User.query.filter_by(email=data['email']).first()
    if user_exists:
        return make_response({"msg": "User already exists"}, 400)

    # Hash the password before storing
    hashed_password = generate_password_hash(data['password'], method='sha256')

    # Create a new user
    new_user = User(name=data['name'], email=data['email'], role=data['role'], location=data['location'], password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return make_response({"msg": "User created successfully"}), 201


# User Login and Generate JWT Token
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    # Validate input
    if not data.get('email') or not data.get('password'):
        return make_response({"msg": "Missing fields"}, 400)

    # Check if user exists
    user = User.query.filter_by(email=data['email']).first()
    if not user or not check_password_hash(user.password, data['password']):
        return make_response({"msg": "Invalid email or password"}), 401

    # Create JWT token
    access_token = create_access_token(identity=user.id)
    user_data = {
        "id": user.id,
        "name": user.name,
        "role": user.role,
        "email": user.email,
        "location": user.location,
    }

    return jsonify(access_token=access_token, user=user_data), 200


# Get current logged-in user's info
@auth_bp.route('/me', methods=['GET'])
@jwt_required()  # Requires a valid JWT token to access
def get_me():
    current_user_id = get_jwt_identity()  # Get the user ID from the JWT
    user = User.query.get(current_user_id)
    if user:
        return jsonify({
            "name": user.name,
            "email": user.email
        }), 200
    return make_response({"msg": "User not found"}), 404

@auth_bp.route('/user', methods=['PATCH'])
@jwt_required()  # Require JWT for authentication
def update_user():
    user_id = request.args.get("user_id")
    if not user_id:
        return make_response({"msg": "User ID is required as a query parameter"}, 400)

    # Ensure that the user is authenticated and only updating their own info
    current_user_id = get_jwt_identity()
    if str(current_user_id) != str(user_id):
        return make_response({"msg": "Unauthorized to update this user's information"}, 403)

    # Retrieve the user to update
    user = User.query.get(user_id)
    if not user:
        return make_response({"msg": "User not found"}, 404)

    # Get data to update
    data = request.get_json()
    
    # Update fields if provided
    if data.get("name"):
        user.name = data["name"]
    if data.get("email"):
        user.email = data["email"]
    if data.get("location"):
        user.location = data["location"]

    # Commit updates to the database
    db.session.commit()

    user_data = {
            "id": user.id,
            "name": user.name,
            "role": user.role,
            "email": user.email,
            "location": user.location,
        }

    return jsonify(user=user_data), 200
