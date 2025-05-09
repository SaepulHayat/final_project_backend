# src/app/services/location_service.py
from ..model.location import Location
from ..model.city import City
from ..model.user import User
from ..extensions import db
from ..utils.validators import validate_location_input
from ..utils.response import success_response, error_response
from sqlalchemy.exc import IntegrityError
import logging
from ..utils.roles import UserRoles

logger = logging.getLogger(__name__)

class LocationService:

    def create_location(self, data, current_user_id, current_user_role):
        logger.debug(f"Attempting to create location. User ID: {current_user_id}, Role: {current_user_role}, Data: {data}")
        errors = validate_location_input(data)
        if errors:
            logger.warning(f"Validation failed for location creation. Errors: {errors}")
            return error_response("Validation failed", errors=errors, status_code=400)

        city_id = data.get('city_id')
        city = City.query.get(city_id)
        if not city:
            logger.warning(f"City with ID {city_id} not found during location creation.")
            return error_response(f"City with ID {city_id} not found", error="invalid_city_id", status_code=400)

        name = data.get('name', "").strip()
        address = data.get('address', "").strip()
        zip_code = data.get('zip_code', "").strip()

        new_location = Location(
            city_id=city_id,
            name=name if name else None,
            address=address if address else None,
            zip_code=zip_code if zip_code else None
        )
        logger.debug(f"New location object created: {new_location}")

        try:
            db.session.add(new_location)
            db.session.flush() # Ensure new_location.id is populated
            logger.info(f"New location (ID: {new_location.id}) added to session and flushed. new_location.id type: {type(new_location.id)}")

            if current_user_role in [UserRoles.CUSTOMER.value, UserRoles.SELLER.value]:
                logger.info(f"User role ({current_user_role}) is CUSTOMER or SELLER. Attempting to assign location to user {current_user_id}.")
                user = User.query.get(current_user_id)
                if user:
                    logger.debug(f"User {current_user_id} (type: {type(current_user_id)}) found. User object: {user}. Current user.location_id: {user.location_id} (type: {type(user.location_id)}).")
                    # Check if user already has a location, handle as per business logic
                    # For now, we assume a user can only be directly linked to one location via user.location_id
                    if user.location_id and user.location_id != new_location.id:
                        logger.warning(f"User {user.id} already has location {user.location_id}. Overwriting with new location {new_location.id}.")
                    
                    logger.debug(f"Attempting to set user.location_id to new_location.id ({new_location.id}).")
                    user.location_id = new_location.id
                    logger.debug(f"After assignment, user.location_id is now: {user.location_id} (type: {type(user.location_id)}).")
                    
                    db.session.add(user) # Add user to session to mark for update
                    logger.info(f"User object (ID: {user.id}) added to session to update location_id to {user.location_id}.")
                else:
                    logger.error(f"User with ID {current_user_id} not found. Cannot assign location. Rolling back location creation.")
                    db.session.rollback() # Rollback location creation if user not found
                    return error_response("Failed to assign location to user, user not found.", status_code=500)
            else:
                logger.info(f"User role ({current_user_role}) is not CUSTOMER or SELLER. Location will not be auto-assigned to user {current_user_id}.")

            logger.info("Attempting to commit session.")
            db.session.commit()
            logger.info(f"Location created and user assignment (if applicable) committed. Location ID: {new_location.id}, User ID: {current_user_id} ({current_user_role}).")
            return success_response("Location created successfully", data=new_location.to_dict(), status_code=201)
        except IntegrityError as e:
            db.session.rollback()
            logger.error(f"Error creating location (IntegrityError): {e}", exc_info=True)
            if "unique constraint" in str(e.orig).lower():
                return error_response("Failed to create location due to a conflict (e.g., duplicate entry).", error="conflict", status_code=409)
            return error_response("Failed to create location due to a database integrity issue.", error=str(e), status_code=500)
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating location: {e}", exc_info=True)
            return error_response("Failed to create location", error=str(e), status_code=500)

    def get_all_locations(self, args, current_user_role):
        if current_user_role != UserRoles.SELLER.value:
            return error_response("Forbidden: You do not have permission to view all locations.", error="insufficient_permissions", status_code=403)

        page = args.get('page', 1, type=int)
        per_page = args.get('per_page', 10, type=int)
        city_id_filter = args.get('city_id', type=int)
        search_term = args.get('search')

        query = Location.query
        if city_id_filter:
            query = query.filter(Location.city_id == city_id_filter)
        if search_term:
            query = query.filter(
                (Location.name.ilike(f'%{search_term}%')) |
                (Location.address.ilike(f'%{search_term}%')) |
                (Location.zip_code.ilike(f'%{search_term}%'))
            )

        try:
            paginated_locations = query.paginate(page=page, per_page=per_page, error_out=False)
            return success_response(
                "Locations retrieved successfully",
                data={
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

    def get_location_by_id(self, location_id, current_user_id, current_user_role):
        location = Location.query.get(location_id)
        if not location:
            return error_response("Location not found", error="not_found", status_code=404)

        is_admin = current_user_role == UserRoles.SELLER.value
        user_is_owner = False

        if not is_admin and current_user_id:
            user = User.query.get(current_user_id)
            if user and user.location_id == location_id:
                user_is_owner = True
        
        if not (is_admin or user_is_owner):
            return error_response("Forbidden: You do not have permission to view this location.", error="insufficient_permissions", status_code=403)

        return success_response("Location found", data=location.to_dict(), status_code=200)

    def update_location(self, location_id, data, current_user_id, current_user_role):
        location = Location.query.get(location_id)
        if not location:
            return error_response("Location not found", error="not_found", status_code=404)

        is_admin = current_user_role == UserRoles.SELLER.value
        user_is_owner = False

        if not is_admin and current_user_id:
            user = User.query.get(current_user_id)
            if user and user.location_id == location_id:
                user_is_owner = True
        
        if not (is_admin or user_is_owner):
            return error_response("Forbidden: You do not have permission to update this location.", error="insufficient_permissions", status_code=403)

        errors = validate_location_input(data, is_update=True)
        if errors:
            return error_response("Validation failed", errors=errors, status_code=400)

        updated = False
        if 'city_id' in data:
            logger.info(f"User {current_user_id} (Role: {current_user_role}) attempting to change city_id for location {location_id}.")
            # Removed admin check for city_id change
            new_city_id = data['city_id']
            city = City.query.get(new_city_id)
            if not city:
                return error_response(f"City with ID {new_city_id} not found for update.", error="invalid_city_id", status_code=400)
            if location.city_id != new_city_id:
                location.city_id = new_city_id
                updated = True

        if 'name' in data:
            normalized_name = data['name'].strip()
            if location.name != normalized_name:
                location.name = normalized_name if normalized_name else None
                updated = True
        if 'address' in data:
            normalized_address = data['address'].strip()
            if location.address != normalized_address:
                location.address = normalized_address if normalized_address else None
                updated = True
        if 'zip_code' in data:
            normalized_zip = data['zip_code'].strip()
            if location.zip_code != normalized_zip:
                location.zip_code = normalized_zip if normalized_zip else None
                updated = True
        
        if not updated:
            return error_response("No update data provided or data is the same as current.", error="no_change", status_code=400)

        try:
            db.session.commit()
            logger.info(f"Location updated: ID {location.id} by user {current_user_id} ({current_user_role}).")
            return success_response("Location updated successfully", data=location.to_dict(), status_code=200)
        except IntegrityError as e:
            db.session.rollback()
            logger.error(f"Error updating location (IntegrityError) {location_id}: {e}", exc_info=True)
            if "unique constraint" in str(e.orig).lower():
                return error_response("Failed to update location due to a conflict.", error="conflict", status_code=409)
            return error_response("Failed to update location due to a database integrity issue.", error=str(e), status_code=500)
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating location {location_id}: {e}", exc_info=True)
            return error_response("Failed to update location", error=str(e), status_code=500)

    def delete_location(self, location_id, current_user_id, current_user_role): # Added current_user_id and current_user_role
        location = Location.query.get(location_id)
        if not location:
            return error_response("Location not found", error="not_found", status_code=404)

        is_admin = current_user_role == UserRoles.SELLER.value
        user_is_owner = False
        current_user = None # Initialize current_user

        if not is_admin: # If not admin, check for ownership
            if not current_user_id: # Should not happen if role_required decorator is working
                return error_response("User identity not found for delete operation.", error="authentication_required", status_code=401)
            
            current_user = User.query.get(current_user_id)
            if not current_user:
                # This case should ideally not happen if JWT identity is valid and user exists
                logger.error(f"User with ID {current_user_id} not found during delete authorization.")
                return error_response("User not found, cannot verify ownership.", status_code=404)

            if current_user.location_id == location_id:
                user_is_owner = True
            
            if not user_is_owner:
                logger.warning(f"User {current_user_id} ({current_user_role}) attempted to delete location {location_id} without ownership.")
                return error_response("Forbidden: You can only delete your own location.", error="insufficient_permissions_delete", status_code=403)
        else: # User is Admin
            logger.info(f"Admin user {current_user_id} performing delete operation on location {location_id}.")


        users_assigned_to_location = User.query.filter(User.location_id == location_id)
        users_to_unassign = []
        is_sole_owner_deleting = False

        if user_is_owner:
            if users_assigned_to_location.count() == 1 and users_assigned_to_location.first().id == current_user_id:
                is_sole_owner_deleting = True
                users_to_unassign.append(current_user)
        elif is_admin: # Admin is deleting
            for user_in_list in users_assigned_to_location.all():
                users_to_unassign.append(user_in_list)


        if not is_admin and not user_is_owner:
            return error_response("Forbidden: You do not have permission to delete this location.", error="insufficient_permissions", status_code=403)

        try:
            # Unassign location from users who are linked to it
            for user_to_update in users_to_unassign:
                user_to_update.location_id = None
                db.session.add(user_to_update)
                logger.info(f"Unassigned location {location_id} from user {user_to_update.id}.")
            
            db.session.delete(location)
            db.session.commit()
            logger.info(f"Location deleted: ID {location_id} by user {current_user_id} ({current_user_role}).")
            return success_response("Location deleted successfully", status_code=200)
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting location {location_id}: {e}", exc_info=True)
            return error_response("Failed to delete location", error=str(e), status_code=500)
