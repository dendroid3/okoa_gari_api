from flask import Blueprint, request, jsonify, make_response
from models import db, Service, User, ServiceUser, Vehicles
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import requests
import base64
from sqlalchemy.exc import IntegrityError
import requests
from datetime import datetime
import base64
from flask import make_response, jsonify, request

service_bp = Blueprint('service_bp', __name__)

@service_bp.route('/', methods=['POST'])
@jwt_required()
def add_service():
    data = request.get_json()
    user_id = get_jwt_identity()

    # return jsonify({"user_id": user_id}), 400
    
    # Validate input
    if not data.get('name') or not data.get('cost'):
        return jsonify({"msg": "Missing fields"}), 400
    
    try:
        # Create and add new service
        new_service = Service(user_id=user_id, name=data['name'], location=data['location'], cost=data['cost'])
        db.session.add(new_service)
        db.session.commit()
        return jsonify({"msg": "Service added successfully"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": str(e)}), 500

@service_bp.route('/', methods=['GET'])
@jwt_required()
def get_services():
    user_id = get_jwt_identity()
    
    # Retrieve services for the logged-in user
    services = Service.query.filter_by(user_id=user_id).all()
    return jsonify([service.to_dict() for service in services]), 200

@service_bp.route('/<int:service_id>', methods=['PUT'])
@jwt_required()
def update_service(service_id):
    data = request.get_json()
    user_id = get_jwt_identity()

    # Validate input
    if not data.get('name') or not data.get('cost'):
        return jsonify({"msg": "Missing fields"}), 400

    try:
        # Find the service by ID and user ID (optional, if you want to ensure the service belongs to the user)
        service = Service.query.filter_by(id=service_id, user_id=user_id).first()
        
        # If the service doesn't exist, return an error
        if not service:
            return jsonify({"msg": "Service not found"}), 404

        # Update the service fields
        service.name = data.get('name')
        service.location = data.get('location')
        service.cost = data.get('cost')

        # Commit the changes to the database
        db.session.commit()
        return jsonify({"msg": "Service updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": str(e)}), 500

@service_bp.route('/<int:service_id>', methods=['DELETE'])
@jwt_required()
def delete_service(service_id):
    try:
        # Find the service by ID and user ID (to ensure the user owns the service)
        service = Service.query.filter_by(id=service_id).first()

        # If the service doesn't exist, return an error
        if not service:
            return jsonify({"msg": "Service not found"}), 404

        service_users = ServiceUser.query.filter_by(service_id=service_id).all()
        for service_user in service_users:
            db.session.delete(service_user)
        db.session.delete(service)
        db.session.commit()
        return jsonify({"msg": "Service deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": str(e)}), 500


@service_bp.route('/all', methods=['GET'])
def get_all_services():
    # Fetch all services along with their associated user data
    services = db.session.query(Service, User).join(User).all()
    
    # Prepare the response with services and user data
    result = []
    for service, user in services:
        result.append({
            'service_id': service.id,
            'service_name': service.name,
            'service_cost': service.cost,
            'service_location': service.location,
            'service_location': service.location,
            'user_id': user.id,
            'user_name': user.name,
            'user_email': user.email,
        })
    
    return jsonify(result), 200

service_user_bp = Blueprint('service_user', __name__)

@service_user_bp.route('/add', methods=['POST'])
@jwt_required()  # This will require a valid JWT token to add a service_user
def add_service_user():
    user_id = get_jwt_identity()  # Get the user ID from the JWT token
    data = request.get_json()

    service_id = data.get('service_id')
    vehicle_id = data.get('vehicle_id')

    if not service_id or not vehicle_id:
        return jsonify({"msg": "Missing service_id or vehicle_id"}), 400

    # Check if service and vehicle exist
    service = Service.query.get(service_id)
    vehicle = Vehicles.query.get(vehicle_id)

    if not service:
        return jsonify({"msg": "Service not found"}), 404
    if not vehicle:
        return jsonify({"msg": "Vehicle not found"}), 404

    # Create a new service_user
    new_service_user = ServiceUser(
        service_id=service_id,
        user_id=user_id,
        vehicle_id=vehicle_id
    )

    try:
        db.session.add(new_service_user)
        db.session.commit()
        return jsonify({"msg": "Service user added successfully"}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"msg": "Service user already exists"}), 400
    
@service_user_bp.route('/all', methods=['GET'])
@jwt_required()  # Ensure the user is authenticated
def get_service_users():
    user_id = get_jwt_identity()  # Get the user ID from the JWT token

    # Query the service_user table and join with service, vehicle, and user (mechanic) to get the full details
    service_users = db.session.query(ServiceUser, Service, Vehicles, User).join(
        Service, ServiceUser.service_id == Service.id
    ).join(
        Vehicles, ServiceUser.vehicle_id == Vehicles.id
    ).join(
        User, Service.user_id == User.id  # Join with User to get mechanic details
    ).filter(ServiceUser.user_id == user_id).all()

    # Format the response
    result = [
        {
            'id': service_user.ServiceUser.id,
            'service_id': service_user.ServiceUser.service_id,
            'service_paid': service_user.ServiceUser.paid, 
            'service_name': service_user.Service.name,
            'service_location': service_user.Service.location,
            'service_cost': service_user.Service.cost,
            'vehicle_id': service_user.ServiceUser.vehicle_id,
            'vehicle_model': service_user.Vehicles.model,
            'vehicle_year': service_user.Vehicles.year,
            'garage_name': service_user.User.name,  # garage name
            'garage_email': service_user.User.email,  # garage phone
            'garage_location': service_user.Service.location  # garage location
        }
        for service_user in service_users
    ]

    return jsonify(result), 200


@service_user_bp.route('/my_requests', methods=['GET'])
@jwt_required()  # Ensure the user is authenticated
def get_mechanic_service_requests():
    mechanic_id = get_jwt_identity()  # Get the user ID (mechanic) from the JWT token

    # Query the services that belong to the mechanic
    services = Service.query.filter_by(user_id=mechanic_id).all()

    if not services:
        return jsonify({"message": "No services found for this mechanic"}), 404

    # Gather the service IDs from the mechanic's services
    service_ids = [service.id for service in services]

    # Query the service_user table to find all service requests (service_users) for these services
    service_requests = db.session.query(ServiceUser, Service, Vehicles, User).join(
        Service, ServiceUser.service_id == Service.id
    ).join(
        Vehicles, ServiceUser.vehicle_id == Vehicles.id
    ).join(
        User, ServiceUser.user_id == User.id  # Join to get the user (customer) who requested the service
    ).filter(ServiceUser.service_id.in_(service_ids)).all()

    # Format the response with service request details
    result = [
        {
            'service_request_id': service_user.ServiceUser.id,
            'service_name': service_user.Service.name,
            'service_paid': service_user.ServiceUser.paid, 
            'service_location': service_user.Service.location,
            'service_cost': service_user.Service.cost,
            'vehicle_model': service_user.Vehicles.model,
            'vehicle_year': service_user.Vehicles.year,
            'customer_name': service_user.User.name,  # Customer's name who requested the service
            'customer_email': service_user.User.email,  # Customer's email
            'vehicle_registration': service_user.Vehicles.registration,
            'created_at': service_user.ServiceUser.created_at
        }
        for service_user in service_requests
    ]

    return jsonify(result), 200

def get_token():
    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    consumer_key = "m8JMckxJn0aRtrqnoqD7ey4jH1w2WYbyhGe4tXGqMF9GxOGC"
    consumer_secret = "NfRXzw0qDCzXdu01TZqB8ojBobIknXCQ5E2BUCAKSEezF2dwrrCUmR4mN9GBk4Ze"
    auth = base64.b64encode(f"{consumer_key}:{consumer_secret}".encode()).decode()

    headers = {
        "Authorization": f"Basic {auth}"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json().get("access_token")
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

@service_bp.route('/pay', methods=['POST'])
def post():
    short_code = 174379
    passkey = "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"
    url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"

    # Get phone and amount from request body
    data = request.json
    phone = data.get("phone")
    amount = data.get("amount")

    if not phone or not amount:
        return make_response(jsonify({"error": "Phone number and amount are required"}), 400)

    # Ensure phone number is correctly formatted
    if phone.startswith("0"):
        phone = phone[1:]  # Remove leading zero
    phone = f"254{phone}"

    token = get_token()
    if not token:
        return make_response(jsonify({"error": "Unable to get token"}), 500)

    date = datetime.now()
    timestamp = date.strftime("%Y%m%d%H%M%S")
    password = base64.b64encode(f"{short_code}{passkey}{timestamp}".encode()).decode()

    mpesa_data = {
        "BusinessShortCode": short_code,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone,
        "PartyB": short_code,
        "PhoneNumber": phone,
        "CallBackURL": "https://mydomain.com/path",
        "AccountReference": "Mpesa Test",
        "TransactionDesc": "Testing stk push"
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        # Make synchronous request using requests
        response = requests.post(url, json=mpesa_data, headers=headers)
        response.raise_for_status()  # Check if request was successful

        service_user = ServiceUser.query.get(data.get("service_user_id"))
        service_user.paid = True
        db.session.commit()
        return jsonify(response.json())

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return make_response(jsonify({"error": "Unable to process STK push", "details": str(e)}), 400)

