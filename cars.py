# cars.py

from flask import Blueprint, request, jsonify, make_response
from models import db, Vehicles, ServiceUser
from flask_jwt_extended import jwt_required, get_jwt_identity

# Define a Blueprint for the cars routes
cars_bp = Blueprint('cars', __name__)

@cars_bp.route('/mine', methods=['POST'])
@jwt_required()  # Require JWT authentication
def create_vehicle():
    data = request.get_json()
    # return data['make']
    # Validate required fields
    required_fields = ['make', 'model', 'year', 'registration', 'transmission', 'fuel_type']
    for field in required_fields:
        if not data.get(field):
            return make_response({"msg": f"Missing field: {field}"}, 400)
    try:
            make = data.get('make')
            model = data.get('model')
            year = int(data.get('year'))  # Convert to integer
            registration = data.get('registration')
            transmission = data.get('transmission')
            fuel_type = data.get('fuel_type')
    except (ValueError, TypeError) as e:
        return make_response({"msg": "Invalid input data format"}, 400)
    # Get the user ID from the JWT token
    user_id = get_jwt_identity()

    # Create a new vehicle
    new_vehicle = Vehicles(
        make=make,
        model=model,
        year = year,
        registration=registration,
        transmission=transmission,
        fuel_type=fuel_type,
        user_id=user_id  # Assuming a relationship between a user and their vehicles
    )

    # Add and commit the new vehicle to the database
    db.session.add(new_vehicle)
    db.session.commit()

    return make_response({"msg": "Vehicle created successfully"}, 201)

@cars_bp.route('/mine', methods=['GET'])
@jwt_required()
def get_vehicles():
    # Get the user ID from the JWT token
    user_id = get_jwt_identity()

    # Query vehicles owned by the authenticated user
    vehicles = Vehicles.query.filter_by(user_id=user_id).all()

    # Format vehicles as a list of dictionaries for JSON serialization
    vehicles_list = [
        {
            "id": vehicle.id,
            "make": vehicle.make,
            "model": vehicle.model,
            "year": vehicle.year,
            "registration": vehicle.registration,
            "transmission": vehicle.transmission,
            "fuel_type": vehicle.fuel_type
        }
        for vehicle in vehicles
    ]

    return make_response(jsonify(vehicles=vehicles_list), 200)

@cars_bp.route('/mine/<int:vehicle_id>', methods=['PUT'])
@jwt_required()  # Require JWT authentication
def update_vehicle(vehicle_id):
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['make', 'model', 'year', 'registration', 'transmission', 'fuel_type']
    for field in required_fields:
        if not data.get(field):
            return make_response({"msg": f"Missing field: {field}"}, 400)
    
    try:
        make = data.get('make')
        model = data.get('model')
        year = int(data.get('year'))  # Convert to integer
        registration = data.get('registration')
        transmission = data.get('transmission')
        fuel_type = data.get('fuel_type')
    except (ValueError, TypeError) as e:
        return make_response({"msg": "Invalid input data format"}, 400)
    
    # Get the user ID from the JWT token
    user_id = get_jwt_identity()

    # Fetch the vehicle by its ID, ensuring the current user is the owner
    vehicle = Vehicles.query.filter_by(id=vehicle_id, user_id=user_id).first()

    if not vehicle:
        return make_response({"msg": "Vehicle not found or you do not have permission to update this vehicle"}, 404)

    # Update the vehicle details
    vehicle.make = make
    vehicle.model = model
    vehicle.year = year
    vehicle.registration = registration
    vehicle.transmission = transmission
    vehicle.fuel_type = fuel_type

    # Commit the changes to the database
    db.session.commit()

    return make_response({"msg": "Vehicle updated successfully"}, 200)

@cars_bp.route('/mine/<int:vehicle_id>', methods=['DELETE'])
@jwt_required()
def delete_vehicle(vehicle_id):
    # Fetch the vehicle by ID
    vehicle = Vehicles.query.get(vehicle_id)
    
    if vehicle:
        # Delete all ServiceUser records associated with this vehicle
        ServiceUser.query.filter_by(vehicle_id=vehicle.id).delete()
        
        # Now delete the vehicle itself
        db.session.delete(vehicle)
        db.session.commit()
        
        return make_response({"msg": "Vehicle deleted successfully"}, 200)
    else:
        return make_response({"msg": "Vehicle not found or unauthorized"}, 404)


def delete_vehicle(vehicle_id):
    # Get the user ID from the JWT token
    user_id = get_jwt_identity()

    # Find the vehicle by ID and ensure it belongs to the authenticated user
    vehicle = Vehicles.query.filter_by(id=vehicle_id, user_id=user_id).first()

    # If vehicle not found or does not belong to the user, return an error
    if not vehicle:
        return make_response({"msg": "Vehicle not found or unauthorized"}, 404)

    # Delete the vehicle
    db.session.delete(vehicle)
    db.session.commit()

    return make_response({"msg": "Vehicle deleted successfully"}, 200)