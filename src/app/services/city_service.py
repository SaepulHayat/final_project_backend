from ..model.city import City
from ..model.state import State # Needed for FK validation
from ..model.location import Location # Needed for delete dependency check
from ..extensions import db
from ..utils.validators import validate_city_input # Assumed
from ..utils.response import success_response, error_response #
from sqlalchemy import func # For case-insensitive checks
from sqlalchemy.exc import IntegrityError # To catch DB errors
import logging

logger = logging.getLogger(__name__)

class CityService:

    def create_city(self, data):
        errors = validate_city_input(data) # Assumed validator
        if errors:
            # Use status_code parameter in error_response
            return error_response("Validation failed", errors=errors, status_code=400)

        # Normalize name (strip, title case)
        name_input = data.get('name', "").strip()
        if not name_input:
            return error_response("Validation failed", errors={'name': 'Name cannot be empty'}, status_code=400)
        name = name_input.title() # Or capitalize() as per guide

        state_id = data.get('state_id')
        if state_id is None: # Ensure state_id is provided
            return error_response("Validation failed", errors={'state_id': 'State ID is required'}, status_code=400)

        # --- Foreign Key Validation ---
        state = State.query.get(state_id)
        if not state:
            return error_response(f"State with id {state_id} not found", error="invalid_state_id", status_code=404) # Or 400 as per guide

        # --- Uniqueness Check (within the state) ---
        existing_city = City.query.filter(
            City.state_id == state_id,
            func.lower(City.name) == func.lower(name)
        ).first()
        if existing_city:
            return error_response(f"City '{name}' already exists in state '{state.name}'", error="duplicate_city_in_state", status_code=409)

        new_city = City(name=name, state_id=state_id)
        try:
            db.session.add(new_city)
            db.session.commit()
            logger.info(f"City created: ID {new_city.id}, Name '{new_city.name}'")
            # Add status_code to success_response
            return success_response("City created successfully", data=new_city.to_dict(), status_code=201)
        except IntegrityError as e: # Catch potential race condition duplicate or other DB issues
            db.session.rollback()
            logger.warning(f"Integrity error creating city '{name}' in state {state_id}: {e}")
            # Re-check for duplicate just in case
            existing_city = City.query.filter(City.state_id == state_id, func.lower(City.name) == func.lower(name)).first()
            if existing_city:
                return error_response(f"City '{name}' already exists in state '{state.name}'", error="duplicate_city_in_state", status_code=409)
            return error_response("Failed to create city due to database error", error=str(e), status_code=500)
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating city '{name}' in state {state_id}: {e}", exc_info=True)
            return error_response("Failed to create city", error=str(e), status_code=500)

    def get_all_cities(self, args):
        # Implement pagination, sorting, filtering by state_id, searching by name
        page = args.get('page', 1, type=int)
        per_page = args.get('per_page', 10, type=int)
        sort_by = args.get('sort_by', 'name')
        order = args.get('order', 'asc')
        state_id_filter = args.get('state_id', type=int)
        search_term = args.get('search')

        query = City.query

        # Filtering
        if state_id_filter:
            query = query.filter(City.state_id == state_id_filter)
        if search_term:
            query = query.filter(City.name.ilike(f'%{search_term}%'))

        # Sorting (ensure valid sort_by column)
        if sort_by == 'name': # Add other valid columns if needed
            sort_column = City.name
        # Add more sortable columns here if needed
        # elif sort_by == 'id':
        #     sort_column = City.id
        else:
            sort_column = City.name # Default sort

        if order == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        try:
            paginated_cities = query.paginate(page=page, per_page=per_page, error_out=False)
            return success_response(
                "Cities retrieved successfully",
                data={
                    # Use the to_dict() method from the model
                    "cities": [city.to_dict() for city in paginated_cities.items],
                    "total": paginated_cities.total,
                    "pages": paginated_cities.pages,
                    "current_page": paginated_cities.page
                },
                status_code=200 # Add status_code
            )
        except Exception as e:
            logger.error(f"Error retrieving cities: {e}", exc_info=True)
            return error_response("Failed to retrieve cities", error=str(e), status_code=500) #

    def get_city_by_id(self, city_id):
        city = City.query.get(city_id)
        if not city:
            return error_response("City not found", error="not_found", status_code=404) #
        # Use the to_dict() method from the model
        # Add status_code to success_response
        return success_response("City found", data=city.to_dict(), status_code=200)

    def update_city(self, city_id, data):
        city = City.query.get(city_id)
        if not city:
            return error_response("City not found", error="not_found", status_code=404) #

        errors = validate_city_input(data, is_update=True) # Assumed validator
        if errors:
            return error_response("Validation failed", errors=errors, status_code=400) #

        updated = False
        new_name_normalized = None
        new_state_id = city.state_id # Keep current state unless changed
        target_state = city.state # Keep current state object unless changed

        if 'state_id' in data:
            potential_new_state_id = data['state_id']
            # --- Foreign Key Validation ---
            if potential_new_state_id != city.state_id:
                new_state = State.query.get(potential_new_state_id)
                if not new_state:
                    return error_response(f"State with id {potential_new_state_id} not found", error="invalid_state_id", status_code=404) # Or 400
                new_state_id = potential_new_state_id # Store the validated new state ID
                target_state = new_state # Store the new state object
                updated = True

        if 'name' in data:
            name_input = data['name'].strip()
            if not name_input:
                return error_response("Validation failed", errors={'name': 'Name cannot be empty'}, status_code=400)
            new_name_normalized = name_input.title() # Or capitalize()

            # Check if name OR state is changing
            if new_name_normalized.lower() != city.name.lower() or new_state_id != city.state_id:
                # --- Uniqueness Check (within the *target* state) ---
                existing_city = City.query.filter(
                    City.id != city_id, # Exclude self
                    City.state_id == new_state_id, # Check in target state
                    func.lower(City.name) == func.lower(new_name_normalized)
                ).first()
                if existing_city:
                    # Use the target_state object fetched earlier or current state if not changing
                    target_state_name = target_state.name
                    return error_response(f"Another city named '{new_name_normalized}' already exists in state '{target_state_name}'", error="duplicate_city_in_state", status_code=409)

                city.name = new_name_normalized
                updated = True
            # Handle case where only casing changes but state remains the same
            elif new_name_normalized != city.name:
                city.name = new_name_normalized
                updated = True


        if not updated:
            return error_response("No update data provided or data matches existing values", error="no_change", status_code=400)

        # Apply state change if validated and different
        if new_state_id != city.state_id:
            city.state_id = new_state_id

        try:
            db.session.commit()
            logger.info(f"City updated: ID {city.id}")
            # Add status_code to success_response
            return success_response("City updated successfully", data=city.to_dict(), status_code=200)
        except IntegrityError as e: # Catch potential race condition duplicate
            db.session.rollback()
            logger.warning(f"Integrity error updating city {city_id}: {e}")
            # Provide a generic conflict message or try to determine the specific conflict if possible
            return error_response("Failed to update city due to potential conflict or database error", error="update_conflict", status_code=409)
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating city {city_id}: {e}", exc_info=True)
            return error_response("Failed to update city", error=str(e), status_code=500)

    def delete_city(self, city_id):
        city = City.query.get(city_id)
        if not city:
            return error_response("City not found", error="not_found", status_code=404) #

        # --- Dependency Check ---
        # Check if any Locations reference this City (more efficient count)
        location_count = db.session.query(func.count(Location.id)).filter(Location.city_id == city_id).scalar()
        if location_count > 0:
            logger.warning(f"Attempt to delete city {city_id} ('{city.name}') failed due to {location_count} dependent locations.")
            return error_response(f"Cannot delete city '{city.name}' because it has {location_count} associated location(s)", error="dependency_exists", status_code=409)

        try:
            city_name = city.name # Store name for logging
            db.session.delete(city)
            db.session.commit()
            logger.info(f"City deleted: ID {city_id}, Name '{city_name}'")
            # Return success, route handler will convert to 204 No Content
            # Add status_code to success_response
            return success_response("City deleted successfully", status_code=200)
        except Exception as e: # Catch potential DB errors
            db.session.rollback()
            logger.error(f"Error deleting city {city_id}: {e}", exc_info=True)
            return error_response("Failed to delete city", error=str(e), status_code=500)

# Responsibilities: Encapsulates business logic for cities, database interactions,
# validation calls, uniqueness checks, foreign key checks, dependency checks (delete),
# normalization, and error handling. Returns structured response dictionaries
# including 'status_code'.