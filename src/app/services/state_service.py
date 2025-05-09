from ..model.state import State
from ..model.country import Country # Needed for FK validation
from ..model.city import City # Needed for dependency check on delete
from ..extensions import db
from ..utils.validators import validate_state_input # Assumed to exist
from ..utils.response import success_response, error_response
from sqlalchemy import func # For case-insensitive checks
from sqlalchemy.exc import IntegrityError # To catch potential DB errors
import logging

logger = logging.getLogger(__name__)

class StateService:

    def create_state(self, data):
        errors = validate_state_input(data) # Basic format validation
        if errors:
            return error_response("Validation failed", errors=errors, status_code=400)

        # Normalize name
        name_input = data.get('name', "").strip()
        if not name_input:
            return error_response("Validation failed", errors={'name': 'Name cannot be empty'}, status_code=400)
        name = name_input.title() # Or capitalize(), adjust as needed

        country_id = data.get('country_id')

        # Foreign Key Validation
        country = Country.query.get(country_id)
        if not country:
            return error_response("Invalid country_id", errors={'country_id': f"Country with id {country_id} not found"}, status_code=400) # Bad request as ID format ok, but not found

        # Uniqueness Check (within the country)
        existing_state = State.query.filter(
            func.lower(State.name) == func.lower(name),
            State.country_id == country_id
        ).first()
        if existing_state:
            return error_response(f"State '{name}' already exists in country '{country.name}'", error="duplicate_state_name", status_code=409) # 409 Conflict

        new_state = State(name=name, country_id=country_id)
        try:
            db.session.add(new_state)
            db.session.commit()
            logger.info(f"State created: ID {new_state.id}, Name '{new_state.name}', Country ID {new_state.country_id}")
            # Eager load country for to_dict or ensure session is active
            db.session.refresh(new_state) # Ensure relationships are loaded if needed immediately
            return success_response("State created successfully", data=new_state.to_dict(), status_code=201)
        except IntegrityError as e: # Catch potential race condition or other constraint violations
            db.session.rollback()
            logger.warning(f"Integrity error creating state '{name}' for country {country_id}: {e}")
            # Check if it's likely the unique constraint again
            return error_response(f"State '{name}' may already exist or another integrity issue occurred.", error="integrity_error", status_code=409)
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating state '{name}': {e}", exc_info=True)
            return error_response("Failed to create state", error=str(e), status_code=500)

    def get_all_states(self, args):
        page = args.get('page', 1, type=int)
        per_page = args.get('per_page', 10, type=int)
        search_term = args.get('search')
        country_id_filter = args.get('country_id', type=int)
        sort_by = args.get('sort_by', 'name') # Default sort
        order = args.get('order', 'asc')

        query = State.query.join(Country) # Join for sorting/filtering by country name if needed later

        # Filtering
        if country_id_filter:
            query = query.filter(State.country_id == country_id_filter)
        if search_term:
            query = query.filter(State.name.ilike(f'%{search_term}%'))

        # Sorting
        sort_column = getattr(State, sort_by, State.name) # Default to name if invalid
        if order.lower() == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        try:
            paginated_states = query.paginate(page=page, per_page=per_page, error_out=False)
            return success_response(
                "States retrieved successfully",
                data={
                    "states": [state.to_dict() for state in paginated_states.items],
                    "total": paginated_states.total,
                    "pages": paginated_states.pages,
                    "current_page": paginated_states.page
                },
                status_code=200
            )
        except Exception as e:
            logger.error(f"Error retrieving states: {e}", exc_info=True)
            return error_response("Failed to retrieve states", error=str(e), status_code=500)

    def get_state_by_id(self, state_id):
        # Eager load country for to_dict()
        state = State.query.options(db.joinedload(State.country)).get(state_id)
        if not state:
            return error_response("State not found", error="not_found", status_code=404)
        return success_response("State found", data=state.to_dict(), status_code=200)

    def get_cities_by_state(self, state_id, args):
        state = State.query.get(state_id)
        if not state:
            return error_response("State not found", error="not_found", status_code=404)

        page = args.get('page', 1, type=int)
        per_page = args.get('per_page', 10, type=int)

        try:
            # Access cities via relationship and paginate
            # Assumes City model has a to_simple_dict() or similar method
            paginated_cities = state.cities.paginate(page=page, per_page=per_page, error_out=False) # Using the relationship directly
            return success_response(
                f"Cities in state '{state.name}' retrieved successfully",
                data={
                    # Use City's to_dict() or to_simple_dict()
                    "cities": [city.to_dict() for city in paginated_cities.items], # Assumes city.to_dict() exists
                    "total": paginated_cities.total,
                    "pages": paginated_cities.pages,
                    "current_page": paginated_cities.page,
                    "state": state.to_dict() # Include state info
                },
                status_code=200
            )
        except Exception as e:
            logger.error(f"Error retrieving cities for state {state_id}: {e}", exc_info=True)
            return error_response("Failed to retrieve cities for state", error=str(e), status_code=500)


    def update_state(self, state_id, data):
        state = State.query.get(state_id)
        if not state:
            return error_response("State not found", error="not_found", status_code=404)

        errors = validate_state_input(data, is_update=True) # Allow partial updates
        if errors:
            return error_response("Validation failed", errors=errors, status_code=400)

        updated = False
        new_name_normalized = None
        new_country_id = state.country_id # Start with current country_id

        if 'country_id' in data:
             potential_new_country_id = data['country_id']
             # Check if changing country
             if potential_new_country_id != state.country_id:
                 # Validate new country_id
                 country = Country.query.get(potential_new_country_id)
                 if not country:
                     return error_response("Invalid country_id", errors={'country_id': f"Country with id {potential_new_country_id} not found"}, status_code=400)
                 # **Caution:** Changing country might have implications. Add business logic if needed.
                 new_country_id = potential_new_country_id # Set the target country_id for uniqueness check
                 state.country_id = new_country_id # Update the object
                 updated = True

        if 'name' in data:
            name_input = data['name'].strip()
            if not name_input:
                return error_response("Validation failed", errors={'name': 'Name cannot be empty'}, status_code=400)

            new_name_normalized = name_input.title() # Or capitalize()

            # Check if name actually changed or if country is changing (requires uniqueness check regardless)
            if new_name_normalized.lower() != state.name.lower() or 'country_id' in data:
                # Uniqueness Check (within the *target* country)
                existing_state = State.query.filter(
                    func.lower(State.name) == func.lower(new_name_normalized),
                    State.country_id == new_country_id, # Check against the potentially new country_id
                    State.id != state_id # Exclude self
                ).first()
                if existing_state:
                     # Fetch target country name for error message if country_id changed
                     target_country_name = Country.query.get(new_country_id).name if new_country_id != state.country_id else state.country.name
                     return error_response(f"Another state named '{new_name_normalized}' already exists in country '{target_country_name}'", error="duplicate_state_name", status_code=409)

                if state.name != new_name_normalized: # Update only if actually different
                    state.name = new_name_normalized
                    updated = True
            # Handle case where only casing changes but name is otherwise the same
            elif state.name != new_name_normalized:
                state.name = new_name_normalized
                updated = True


        if not updated:
            return error_response("No update data provided or data is the same as current", error="no_change", status_code=400)

        try:
            db.session.commit()
            logger.info(f"State updated: ID {state.id}, New Name '{state.name}', New Country ID {state.country_id}")
            db.session.refresh(state) # Refresh to get updated relationship data if needed (e.g., country name)
            return success_response("State updated successfully", data=state.to_dict(), status_code=200)
        except IntegrityError as e: # Catch potential race condition duplicate
            db.session.rollback()
            logger.warning(f"Integrity error updating state {state_id} to '{new_name_normalized}': {e}")
            return error_response(f"Another state named '{new_name_normalized}' may already exist or another integrity issue occurred.", error="integrity_error", status_code=409)
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating state {state_id}: {e}", exc_info=True)
            return error_response("Failed to update state", error=str(e), status_code=500)

    def delete_state(self, state_id):
        state = State.query.get(state_id)
        if not state:
            return error_response("State not found", error="not_found", status_code=404)

        # **Dependency Check (Crucial)**
        # Check if any cities are linked before deleting, even with cascade.
        # This prevents accidental mass deletion via cascade and is safer for admin actions.
        city_count = state.cities.count() # Efficiently check if related cities exist
        if city_count > 0:
            logger.warning(f"Attempted to delete state {state_id} ('{state.name}') which has {city_count} associated cities.")
            return error_response(
                f"Cannot delete state '{state.name}' because it has {city_count} associated cities. Please delete or reassign the cities first.",
                error="dependency_exists",
                status_code=409 # 409 Conflict indicates the resource cannot be deleted in its current state
            )

        # If the check passes (or is omitted), proceed with deletion.
        # The cascade="all, delete-orphan" on the relationship in state.py
        # means SQLAlchemy would handle city deletion *if* this check wasn't here.
        # But the explicit check returning 409 is preferred.

        try:
            state_name = state.name # Store for logging
            db.session.delete(state)
            db.session.commit()
            logger.info(f"State deleted: ID {state_id}, Name '{state_name}'")
            # Service returns success dict, route handler converts to 204
            return success_response("State deleted successfully", status_code=200)
        except Exception as e: # Catch potential DB errors during delete
            db.session.rollback()
            logger.error(f"Error deleting state {state_id}: {e}", exc_info=True)
            return error_response("Failed to delete state", error=str(e), status_code=500)