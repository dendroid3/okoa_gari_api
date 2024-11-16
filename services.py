from flask import Blueprint, request, jsonify
from models import db, Service, User, ServiceUser, Vehicles
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError

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
        new_service = Service(user_id=user_id, name=data['name'], cost=data['cost'])
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
            'user_id': user.id,
            'user_name': user.name,
            'user_email': user.email,
            'user_location': user.location
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
            'service_id': service_user.ServiceUser.service_id,
            'service_name': service_user.Service.name,
            'service_cost': service_user.Service.cost,
            'vehicle_id': service_user.ServiceUser.vehicle_id,
            'vehicle_model': service_user.Vehicles.model,
            'vehicle_year': service_user.Vehicles.year,
            'mechanic_name': service_user.User.name,  # Mechanic name
            'mechanic_email': service_user.User.email,  # Mechanic phone
            'mechanic_location': service_user.User.location  # Mechanic location
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
