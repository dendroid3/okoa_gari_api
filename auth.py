from flask import Blueprint, request, jsonify, make_response, current_app
from models import db, User
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import aliased
from sqlalchemy import func
from models import db, Service, User, ServiceUser, Vehicles
import random
from datetime import datetime, timedelta
import string

from flask_mail import Message as MailMessage

otp_store = {}

# Create a blueprint for authentication routes
auth_bp = Blueprint('auth', __name__)

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

def send_email(to_email, subject, content):

    # Create the email message
    msg = MailMessage(subject=subject, recipients=[to_email], body=content)
    try:
        print("The /test route was accessed!")
        print(f"2FA Email Body: {content}")
        mail = current_app.extensions['mail']
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


# Register User
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    # Validate input
    if not data.get('name') or not data.get('email') or not data.get('password') or not data.get('role'):
        return make_response({"msg": "Missing fields"}, 400)

    # Check if user already exists
    user_exists = User.query.filter_by(email=data['email']).first()
    if user_exists:
        return make_response({"msg": "User already exists"}, 400)

    # Hash the password before storing
    hashed_password = generate_password_hash(data['password'], method='sha256')

    # Create a new user
    new_user = User(name=data['name'], email=data['email'], role=data['role'], password=hashed_password)
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
    
    email = data.get('email')
    # Generate 2FA code
    otp = generate_otp()
    otp_store[email] = {
        'otp': otp,
        'expiry': datetime.now() + timedelta(minutes=5)  # OTP expires in 5 minutes
    }

    # Send OTP to the user's email
    subject = "Verification Code"
    content = f"Your verification code is {otp}. It will expire in 5 minutes."
    if send_email(email, subject, content):  # Pass 'mail' here
        
        return {'message': 'Please verify your 2FA code sent to your email'}, 200

    return {'message': 'Failed to send 2FA code'}, 500

@auth_bp.route('/otp', methods=['POST'])
def verify_otp():
    data = request.get_json()
    email = data.get('email')
    otp = data.get('otp')

    if email in otp_store:
        stored_otp = otp_store[email]['otp']
        expiry = otp_store[email]['expiry']
        if datetime.now() > expiry:
            return {'message': 'OTP expired'}, 400
        if otp == stored_otp:
            del otp_store[email]  # Remove OTP after successful verification
            # Create JWT token
            user = User.query.filter_by(email=data['email']).first()
            access_token = create_access_token(identity=user.id)
            user_data = {
                "id": user.id,
                "name": user.name,
                "role": user.role,
                "email": user.email,
            }

            return jsonify(access_token=access_token, user=user_data), 200
        return {'message': 'Invalid OTP'}, 400

    return {'message': 'No OTP found for email'}, 400

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
   
    # Commit updates to the database
    db.session.commit()

    user_data = {
            "id": user.id,
            "name": user.name,
            "role": user.role,
            "email": user.email,
        }

    return jsonify(user=user_data), 200

@auth_bp.route('/mechanics', methods=['GET'])
@jwt_required()  # Require JWT authentication to access the mechanics list
def get_mechanics():
    # Query users with the role of 'mechanic' and include the number of services they are associated with
    mechanics = db.session.query(
        User.id,
        User.name,
        User.email,
        User.role,
        func.count(Service.id).label('number_of_services')
    ).join(Service, Service.user_id == User.id, isouter=True) \
     .filter(User.role == 'garage') \
     .group_by(User.id) \
     .all()

    # If no mechanics are found, return an error message
    if not mechanics:
        return make_response({"msg": "No mechanics found"}, 404)

    # Format mechanics as a list of dictionaries for JSON serialization
    mechanics_list = [
        {
            "id": mechanic.id,
            "name": mechanic.name,
            "email": mechanic.email,
            "role": mechanic.role,
            "number_of_services": mechanic.number_of_services
        }
        for mechanic in mechanics
    ]

    return make_response(jsonify(mechanics_list), 200)

@auth_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()  # Require JWT authentication to delete a user
def delete_user(user_id):
    # Find the user by ID
    user = User.query.get(user_id)

    # If the user doesn't exist, return an error
    if not user:
        return make_response({"msg": "User not found"}, 404)

    try:
        # Delete all service_user records associated with the user's services
        services_to_delete = Service.query.filter_by(user_id=user_id).all()
        for service in services_to_delete:
            # Delete all service_user records where service_id matches the current service.id
            service_users_to_delete = ServiceUser.query.filter_by(service_id=service.id).all()
            for service_user in service_users_to_delete:
                db.session.delete(service_user)  # Delete each service_user record

            # Delete the service itself
            db.session.delete(service)  # Delete each service

        # Now delete the user
        db.session.delete(user)
        db.session.commit()

        return make_response({"msg": "User, associated services, and service_users deleted successfully"}, 200)

    except Exception as e:
        db.session.rollback()
        return make_response({"msg": f"Error deleting user, services, and service_users: {str(e)}"}, 500)
