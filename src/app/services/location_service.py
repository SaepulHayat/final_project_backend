# src/app/services/location_service.py
from ..model.location import Location
from ..model.city import City
from ..model.user import User # For dependency check
from ..extensions import db
from ..utils.validators import validate_location_input # Assuming this exists
from ..utils.response import success_response, error_response
from sqlalchemy.exc import IntegrityError
import logging
from ..utils.roles import UserRoles # Assuming UserRoles enum

logger = logging.getLogger(__name__)

class LocationService:

    def create_location(self, data):
        errors = validate_location_input(data)
        if errors:
            return error_response("Validation failed", errors=errors, status_code=400)

        # --- Foreign Key Validation ---
        city_id = data.get('city_id')
        city = City.query.get(city_id)
        if not city:
            return error_response(f"City with ID {city_id} not found", error="invalid_city_id", status_code=404) # Or 400

        # --- Normalization ---
        name = data.get('name', "").strip()
        address = data.get('address', "").strip()
        zip_code = data.get('zip_code', "").strip()
        # Potentially apply .title() or other normalization

        # --- Create Location ---
        new_location = Location(
            city_id=city_id,
            name=name if name else None, # Handle empty strings if nullable
            address=address if address else None,
            zip_code=zip_code if zip_code else None
        )

        try:
            db.session.add(new_location)
            db.session.commit()
            logger.info(f"Location created: ID {new_location.id}")
            # Use the model's to_dict() for response
            return success_response("Location created successfully", data=new_location.to_dict(), status_code=201)
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating location: {e}", exc_info=True)
            return error_response("Failed to create location", error=str(e), status_code=500)

    def get_all_locations(self, args, current_user_role): # Pass role for authorization
        # --- Authorization ---
        # Typically Admin only for listing all raw locations
        if current_user_role != UserRoles.ADMIN.value: # Assuming UserRoles enum
             return error_response("Forbidden", error="insufficient_permissions", status_code=403)

        # --- Pagination, Filtering, Sorting, Searching ---
        page = args.get('page', 1, type=int)
        per_page = args.get('per_page', 10, type=int)
        city_id_filter = args.get('city_id', type=int)
        search_term = args.get('search')
        # Add sorting logic based on args

        query = Location.query
        if city_id_filter:
            query = query.filter(Location.city_id == city_id_filter)
        if search_term:
             query = query.filter(
                 (Location.name.ilike(f'%{search_term}%')) |
                 (Location.address.ilike(f'%{search_term}%')) |
                 (Location.zip_code.ilike(f'%{search_term}%'))
             )
        # Add query.order_by(...)

        try:
            paginated_locations = query.paginate(page=page, per_page=per_page, error_out=False)
            return success_response(
                "Locations retrieved successfully",
                data={
                    # Use model's to_dict()
                    "locations": [loc.to_dict() for loc in paginated_locations.items],
                    "total": paginated_locations.total,
                    "pages": paginated_locations.pages,
                    "current_page": paginated_locations.page
                },
                status_code=200
            )
        except Exception as e:
            logger.error(f"Error retrieving locations: {e}", exc_info=True)
            return error_response("Failed to retrieve locations", error=str(e), status_code=500)

    def get_location_by_id(self, location_id, current_user_id, current_user_role): # Pass user info
        location = Location.query.get(location_id)
        if not location:
            return error_response("Location not found", error="not_found", status_code=404)

        # --- Authorization ---
        # Check if Admin OR if the user's location_id matches
        user_is_owner = False
        if current_user_id:
            user = User.query.get(current_user_id) # Or get from cache
            if user and user.location_id == location_id:
                user_is_owner = True

        if not (current_user_role == UserRoles.ADMIN.value or user_is_owner):
             return error_response("Forbidden", error="insufficient_permissions", status_code=403)

        # Use model's to_dict()
        return success_response("Location found", data=location.to_dict(), status_code=200)

    def update_location(self, location_id, data, current_user_id, current_user_role): # Pass user info
        location = Location.query.get(location_id)
        if not location:
            return error_response("Location not found", error="not_found", status_code=404)

        # --- Authorization ---
        user_is_owner = False
        if current_user_id:
            user = User.query.get(current_user_id) # Or get from cache
            if user and user.location_id == location_id:
                user_is_owner = True

        is_admin = current_user_role == UserRoles.ADMIN.value

        if not (is_admin or user_is_owner):
             return error_response("Forbidden", error="insufficient_permissions", status_code=403)

        # --- Validation (Partial) ---
        errors = validate_location_input(data, is_update=True)
        if errors:
            return error_response("Validation failed", errors=errors, status_code=400)

        updated = False
        # --- Field Restrictions & Updates ---
        if 'city_id' in data:
            if not is_admin: # Regular user cannot change city_id
                 return error_response("Forbidden: Only Admins can change the city.", error="permission_denied", status_code=403)
            new_city_id = data['city_id']
            city = City.query.get(new_city_id)
            if not city:
                return error_response(f"City with ID {new_city_id} not found", error="invalid_city_id", status_code=404) # or 400
            if location.city_id != new_city_id:
                location.city_id = new_city_id
                updated = True

        # Fields updatable by owner or admin
        if 'name' in data:
            normalized_name = data['name'].strip() # Normalize
            if location.name != normalized_name:
                location.name = normalized_name
                updated = True
        if 'address' in data:
             normalized_address = data['address'].strip() # Normalize
             if location.address != normalized_address:
                 location.address = normalized_address
                 updated = True
        if 'zip_code' in data:
             normalized_zip = data['zip_code'].strip() # Normalize
             if location.zip_code != normalized_zip:
                 location.zip_code = normalized_zip
                 updated = True

        if not updated:
            return error_response("No update data provided or data is the same", error="no_change", status_code=400)

        try:
            db.session.commit()
            logger.info(f"Location updated: ID {location.id}")
            # Use model's to_dict()
            return success_response("Location updated successfully", data=location.to_dict(), status_code=200)
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating location {location_id}: {e}", exc_info=True)
            return error_response("Failed to update location", error=str(e), status_code=500)

    def delete_location(self, location_id):
        # Authorization should be checked in the route (Admin only)
        location = Location.query.get(location_id)
        if not location:
            return error_response("Location not found", error="not_found", status_code=404)

        # --- Dependency Check ---
        # CRUCIAL: Check if any User is using this location
        associated_user = User.query.filter_by(location_id=location_id).first() # Efficient check
        if associated_user:
            logger.warning(f"Attempted to delete location {location_id} which is referenced by user {associated_user.id}")
            return error_response(
                "Location cannot be deleted because it is currently assigned to one or more users.",
                error="dependency_exists",
                status_code=409 # 409 Conflict
            )

        try:
            db.session.delete(location)
            db.session.commit()
            logger.info(f"Location deleted: ID {location_id}")
            # Success response will be converted to 204 by route
            return success_response("Location deleted successfully", status_code=200)
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting location {location_id}: {e}", exc_info=True)
            return error_response("Failed to delete location", error=str(e), status_code=500)