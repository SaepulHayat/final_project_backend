# Guide: Implementing State CRUD Operations

This guide details how to implement Create, Read, Update, and Delete (CRUD) operations for the `State` model, adhering to a layered architecture and incorporating recommended measures.

**Reference:**

- State Model: `state.py`
- Country Model (for relationship): `country.py`
- City Model (for relationship): `city.py`

## 1. Model Layer (`src/app/model/state.py`)

- **Existing Model:** The State model includes `id`, `name` (required), and `country_id` (required foreign key).
- **Relationships:**
  - Many-to-One with `Country` (`country` backref).
  - One-to-Many with `City` (`cities` backref, `lazy='dynamic'`, `cascade="all, delete-orphan"`).
- **Responsibilities:** Defines the data structure and database mapping for states.
- **Serialization:** The existing `to_dict()` method provides a good representation. We can add a `to_simple_dict` if a less detailed view is needed elsewhere.

  ```python
  # Inside State class in state.py

  def to_dict(self):
      """Returns a dictionary representation of the state."""
      return {
          'id': self.id,
          'name': self.name,
          'country_id': self.country_id,
          'country_name': self.country.name if self.country else None
      }

  # Optional: Add if needed for scenarios requiring only id/name
  # def to_simple_dict(self):
  #     """Returns a simple dictionary representation of the state."""
  #     return {
  #         'id': self.id,
  #         'name': self.name
  #     }
  ```

## 2. Utility Layer (`src/app/utils/`)

- **Validators (`validators.py`):**
  - Create a validation function: `validate_state_input(data, is_update=False)`
  - Checks:
    - `name`: Required (unless `is_update`), non-empty string, length constraints (e.g., 100).
    - `country_id`: Required (unless `is_update`), must be a valid integer. (Existence check performed in the service layer).
  - Return a dictionary of errors if validation fails, otherwise `None`.
- **Response Formatting (`response.py`):**
  - Utilize the existing `success_response`, `error_response`, and `create_response` functions for consistent API responses.
- **Decorators (`decorators.py`):**
  - Use `@jwt_required()` for endpoints requiring authentication (Create, Update, Delete).
  - Use `@admin_required` (based on `role_required([UserRoles.ADMIN.value])` from `decorators.py`) to enforce permissions for CUD operations.

## 3. Service Layer (`src/app/services/state_service.py`)

- **Create State Service Class:**

  ```python
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

  # Responsibilities: Encapsulates business logic for states, interacts with State, Country, City models,
  # performs validation (format, FK existence, uniqueness), normalization, handles relationships
  # (dependency check on delete), manages errors, and structures responses.
  ```

## 4. Route Layer (`src/app/routes/state_route.py`)

- **Create Blueprint and Import Services/Utils:**

  ```python
  from flask import Blueprint, request, jsonify
  from ..services.state_service import StateService
  from ..utils.response import create_response # Use create_response
  from ..utils.decorators import jwt_required, admin_required # Use admin_required
  # from ..utils.roles import UserRoles # No direct use needed if using admin_required
  import logging

  logger = logging.getLogger(__name__)

  state_bp = Blueprint('states', __name__, url_prefix='/api/v1/states')
  state_service = StateService()

  @state_bp.route('/', methods=['POST'])
  @jwt_required()
  @admin_required # Admin role required
  def create_state_route():
      data = request.get_json()
      if not data:
          return create_response(status="error", message="Request body must be JSON"), 400

      result = state_service.create_state(data)
      status_code = result.pop('status_code', 500) # Remove status_code before passing to create_response
      return create_response(**result), status_code

  @state_bp.route('/', methods=['GET'])
  # Public endpoint - no @jwt_required or @admin_required
  def get_states_route():
      args = request.args # For pagination/filtering/sorting/searching
      result = state_service.get_all_states(args)
      status_code = result.pop('status_code', 500)
      return create_response(**result), status_code

  @state_bp.route('/<int:state_id>', methods=['GET'])
  # Public endpoint
  def get_state_by_id_route(state_id):
      result = state_service.get_state_by_id(state_id)
      status_code = result.pop('status_code', 500)
      return create_response(**result), status_code

  @state_bp.route('/<int:state_id>/cities', methods=['GET'])
  # Public endpoint - Get cities within a specific state
  def get_cities_by_state_route(state_id):
      args = request.args # For pagination
      result = state_service.get_cities_by_state(state_id, args)
      status_code = result.pop('status_code', 500)
      return create_response(**result), status_code

  @state_bp.route('/<int:state_id>', methods=['PATCH']) # Using PATCH for partial updates
  @jwt_required()
  @admin_required # Admin role required
  def update_state_route(state_id):
      data = request.get_json()
      if not data:
          return create_response(status="error", message="Request body must be JSON"), 400

      result = state_service.update_state(state_id, data)
      status_code = result.pop('status_code', 500)
      return create_response(**result), status_code

  @state_bp.route('/<int:state_id>', methods=['DELETE'])
  @jwt_required()
  @admin_required # Admin role required
  def delete_state_route(state_id):
      result = state_service.delete_state(state_id)
      status_code = result.pop('status_code', 500)

      # Handle 204 No Content for successful deletion
      if result.get('status') == 'success' and status_code == 200: # Service signals success with 200
          return "", 204 # Return empty body with 204 status
      # Otherwise, return the JSON response from the service (e.g., 404, 409, 500)
      return create_response(**result), status_code

  # Register blueprint in app factory (e.g., in app/__init__.py)
  # from .routes.state_route import state_bp
  # app.register_blueprint(state_bp)

  # Responsibilities: Defines API endpoints, handles HTTP requests/responses, parses data,
  # calls StateService, applies security decorators, formats final JSON output using create_response.
  ```

## 5. Key Considerations & Error Handling

- **Role-Based Access Control (RBAC):**
  - **Public Read:** Listing states (`GET /`), getting a specific state (`GET /{id}`), and listing its cities (`GET /{id}/cities`) are public.
  - **Admin CUD:** Creating (`POST /`), updating (`PATCH /{id}`), and deleting (`DELETE /{id}`) states require Admin privileges via `@admin_required`.
- **Input Validation:**
  - Basic format validation (e.g., field types, presence for create) in `StateService` via `validate_state_input`.
  - Foreign key (`country_id`) existence is checked within the service methods (`create_state`, `update_state`).
  - Returns `400 Bad Request` for validation errors.
- **Normalization:**
  - State `name` is normalized (e.g., `strip()`, `title()`) before saving/updating.
- **Uniqueness Constraint:**
  - A state `name` should be unique _within a given country_.
  - Explicit, case-insensitive checks are performed in `create_state` and `update_state` service methods against the target `country_id` before database operations, returning `409 Conflict`.
  - `IntegrityError` is caught during commit as a fallback.
- **Error Handling Strategy:**
  - **Service Layer:** Returns dictionaries with status, message, data/error details, and `status_code`. Handles specific errors like `not_found` (404), `duplicate_state_name` (409), `dependency_exists` (409), `integrity_error` (409), validation errors (400), and general failures (500).
  - **Route Layer:** Uses `create_response` to format the JSON output based on the service's response dictionary. Translates successful deletions (indicated by the service with `200 OK`) into a `204 No Content` HTTP response.
- **Relationship Management (Deletion):**
  - **Crucial:** The `delete_state` service method includes an explicit check for dependent `City` records.
  - If dependent cities exist, the deletion is blocked, and a `409 Conflict` error is returned. This is preferred over relying solely on `cascade="all, delete-orphan"` to prevent accidental data loss.
- **Pagination & Filtering:**
  - Implemented in `get_all_states` service method using SQLAlchemy's `paginate()`.
  - Supports `page`, `per_page`, `search` (by name), `country_id` filtering, and `sort_by`/`order` parameters via `request.args` in the route.
  - Implemented for `get_cities_by_state` as well.
- **Serialization (`to_dict()`):**
  - The `to_dict()` method on the `State` model controls the API response structure, including the `country_name`. Ensure related models (`City`) also have appropriate serialization methods.

By following these steps, you can implement robust CRUD operations for the `State` model, consistent with the application's architecture and the specific recommendations from `guide_state.md`.
