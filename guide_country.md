# Guide: Implementing Country CRUD Operations

This guide details how to implement Create, Read, Update, and Delete (CRUD) operations for the `Country` model, adhering to a layered architecture.

**Reference:**

- Country Model: `country.py`
- State Model (for relationship): `state.py`
- Recommended Measures: `guide_country.md`
- Decorators: `decorators.py`
- Response Utilities: `response.py`

## 1. Model Layer (`src/app/model/country.py`)

- **Existing Model:** The `Country` model includes `id` (Primary Key), `name` (String, unique, non-nullable), and `code` (String, unique, nullable).
- **Relationship:** It has a one-to-many relationship with the `State` model (`states` backref, `lazy='dynamic'`, `cascade="all, delete-orphan"`).
- **Responsibilities:** Defines the data structure and database mapping for countries.
- **Serialization:** Implement `to_dict()` for API responses.

  ```python
  # Inside Country class in country.py
  def to_dict(self):
      """Returns a dictionary representation of the country."""
      return {
          'id': self.id,
          'name': self.name,
          'code': self.code
      }
  ```

  A `to_simple_dict()` can also be added if a less detailed representation is needed for embedding in other objects, though `to_dict()` is already quite simple for `Country`.

## 2. Utility Layer (`src/app/utils/`)

- **Validators (`validators.py`):**

  - Create a validation function: `validate_country_input(data, is_update=False)`
  - Checks:
    - `name`: Required (unless `is_update` and not provided), non-empty string, max length (e.g., 100).
    - `code`: Optional. If provided, non-empty string, max length (e.g., 10).
  - Return a dictionary of errors if validation fails, otherwise `None`.

- **Response Formatting (`response.py`):**

  - Utilize `success_response`, `error_response`, and `create_response` functions for consistent API responses.

- **Decorators (`decorators.py`):**
  - Use `@jwt_required()` for authenticated endpoints.
  - Use a role-checking decorator like `@role_required(UserRoles.ADMIN)` for operations requiring Admin privileges (Create, Update, Delete).

## 3. Service Layer (`src/app/services/country_service.py`)

- **Create CountryService Class:**

  ```python
  from ..model.country import Country
  from ..model.state import State # For checking states linked to a country
  from ..extensions import db
  from ..utils.validators import validate_country_input # Assuming this will be created
  from ..utils.response import success_response, error_response
  from sqlalchemy import func
  from sqlalchemy.exc import IntegrityError
  import logging

  logger = logging.getLogger(__name__)

  class CountryService:

      def create_country(self, data):
          errors = validate_country_input(data)
          if errors:
              return error_response("Validation failed", errors=errors, status_code=400)

          name_input = data.get('name', "").strip()
          code_input = data.get('code', "").strip() if data.get('code') is not None else None

          if not name_input:
               return error_response("Validation failed", errors={'name': 'Name cannot be empty'}, status_code=400)

          name = name_input.title() # Normalize name
          code = code_input.upper() if code_input else None # Normalize code

          # Uniqueness checks
          if Country.query.filter(func.lower(Country.name) == func.lower(name)).first():
              return error_response(f"Country name '{name}' already exists", error="duplicate_name", status_code=409)
          if code and Country.query.filter(func.lower(Country.code) == func.lower(code)).first():
              return error_response(f"Country code '{code}' already exists", error="duplicate_code", status_code=409)

          new_country = Country(name=name, code=code)
          try:
              db.session.add(new_country)
              db.session.commit()
              logger.info(f"Country created: ID {new_country.id}, Name '{new_country.name}'")
              return success_response("Country created successfully", data=new_country.to_dict(), status_code=201)
          except IntegrityError as e: # Fallback for race conditions
              db.session.rollback()
              logger.warning(f"Integrity error creating country '{name}': {e}")
              # Determine if it was name or code uniqueness based on error if possible, or be generic
              return error_response(f"Country name or code already exists", error="duplicate_entry", status_code=409)
          except Exception as e:
              db.session.rollback()
              logger.error(f"Error creating country '{name}': {e}", exc_info=True)
              return error_response("Failed to create country", error=str(e), status_code=500)

      def get_all_countries(self, args):
          page = args.get('page', 1, type=int)
          per_page = args.get('per_page', 10, type=int)
          search_term = args.get('search')
          sort_by = args.get('sort_by', 'name') # Default sort by name
          order = args.get('order', 'asc') # Default order ascending

          query = Country.query

          if search_term: # Filter by name or code
              query = query.filter(
                  db.or_(
                      Country.name.ilike(f'%{search_term}%'),
                      Country.code.ilike(f'%{search_term}%')
                  )
              )

          if sort_by == 'name':
              order_column = Country.name
          elif sort_by == 'code':
              order_column = Country.code
          else: # Default or invalid sort_by
              order_column = Country.name

          if order.lower() == 'desc':
              query = query.order_by(order_column.desc())
          else:
              query = query.order_by(order_column.asc())

          try:
              paginated_countries = query.paginate(page=page, per_page=per_page, error_out=False)
              return success_response(
                  "Countries retrieved successfully",
                  data={
                      "countries": [country.to_dict() for country in paginated_countries.items],
                      "total": paginated_countries.total,
                      "pages": paginated_countries.pages,
                      "current_page": paginated_countries.page
                  },
                  status_code=200
              )
          except Exception as e:
              logger.error(f"Error retrieving countries: {e}", exc_info=True)
              return error_response("Failed to retrieve countries", error=str(e), status_code=500)

      def get_country_by_id(self, country_id):
          # Ensure country_id is valid integer format (handled by route typically)
          country = Country.query.get(country_id)
          if not country:
              return error_response("Country not found", error="not_found", status_code=404)
          return success_response("Country found", data=country.to_dict(), status_code=200)

      def get_states_by_country(self, country_id, args):
          country = Country.query.get(country_id)
          if not country:
              return error_response("Country not found", error="not_found", status_code=404)

          page = args.get('page', 1, type=int)
          per_page = args.get('per_page', 10, type=int)
          # Add sorting for states if needed, e.g., by state.name

          try:
              # Assuming State model has to_simple_dict() or to_dict()
              paginated_states = State.query.with_parent(country).order_by(State.name.asc()).paginate(page=page, per_page=per_page, error_out=False)
              return success_response(
                  f"States in country '{country.name}' retrieved successfully",
                  data={
                      "states": [state.to_dict() for state in paginated_states.items], # Or state.to_simple_dict()
                      "total": paginated_states.total,
                      "pages": paginated_states.pages,
                      "current_page": paginated_states.page,
                      "country": country.to_dict() # Or country.to_simple_dict()
                  },
                  status_code=200
              )
          except Exception as e:
              logger.error(f"Error retrieving states for country {country_id}: {e}", exc_info=True)
              return error_response("Failed to retrieve states for country", error=str(e), status_code=500)

      def update_country(self, country_id, data):
          country = Country.query.get(country_id)
          if not country:
              return error_response("Country not found", error="not_found", status_code=404)

          errors = validate_country_input(data, is_update=True)
          if errors:
              return error_response("Validation failed", errors=errors, status_code=400)

          updated = False
          new_name_title_cased = None
          new_code_upper_cased = None

          if 'name' in data:
              name_input = data['name'].strip()
              if not name_input:
                  return error_response("Validation failed", errors={'name': 'Name cannot be empty'}, status_code=400)
              new_name_title_cased = name_input.title()
              if new_name_title_cased.lower() != country.name.lower():
                  existing_country = Country.query.filter(
                      func.lower(Country.name) == func.lower(new_name_title_cased),
                      Country.id != country_id
                  ).first()
                  if existing_country:
                      return error_response(f"Another country with the name '{new_name_title_cased}' already exists", error="duplicate_name", status_code=409)
                  country.name = new_name_title_cased
                  updated = True
              elif new_name_title_cased != country.name: # Case change only
                  country.name = new_name_title_cased
                  updated = True

          if 'code' in data:
              code_input = data['code'].strip() if data['code'] is not None else None
              if code_input is not None and not code_input: # if "code": ""
                   return error_response("Validation failed", errors={'code': 'Code cannot be an empty string if provided, or omit the key to keep it unchanged/null.'}, status_code=400)
              new_code_upper_cased = code_input.upper() if code_input else None

              if (new_code_upper_cased and country.code and new_code_upper_cased.lower() != country.code.lower()) or \
                 (new_code_upper_cased and not country.code) or \
                 (not new_code_upper_cased and country.code): # Code is changing
                  if new_code_upper_cased:
                      existing_country_code = Country.query.filter(
                          func.lower(Country.code) == func.lower(new_code_upper_cased),
                          Country.id != country_id
                      ).first()
                      if existing_country_code:
                          return error_response(f"Another country with the code '{new_code_upper_cased}' already exists", error="duplicate_code", status_code=409)
                  country.code = new_code_upper_cased
                  updated = True
              elif new_code_upper_cased and country.code and new_code_upper_cased != country.code: # Case change only for code
                  country.code = new_code_upper_cased
                  updated = True


          if not updated and data: # Check if data was provided but no actual changes made
               # If only name was provided and it's the same
              if 'name' in data and 'code' not in data and new_name_title_cased == country.name:
                  return error_response("Provided name is the same as the current name.", error="no_change", status_code=400)
              # If only code was provided and it's the same
              if 'code' in data and 'name' not in data and new_code_upper_cased == country.code:
                   return error_response("Provided code is the same as the current code.", error="no_change", status_code=400)
              # If both provided and both are same
              if 'name' in data and 'code' in data and new_name_title_cased == country.name and new_code_upper_cased == country.code:
                  return error_response("Provided name and code are the same as the current values.", error="no_change", status_code=400)
              # If 'name' in data and 'code' not in data (and name not changed, handled above), it's not an error if name was the only field.
              # Same for code. The logic implies that if `updated` is false, and `data` was present, no effective change occurred.
              # This more generic message can be used if specific field checks are complex.
              return error_response("No update data provided or data matches current values.", error="no_change", status_code=400)


          if not data: # No data in request payload
              return error_response("No update data provided", error="no_data", status_code=400)

          if not updated: # If after all checks, nothing was changed (e.g. only non-model fields sent)
               return error_response("No effective change in provided data.", error="no_effective_change", status_code=400)


          try:
              db.session.commit()
              logger.info(f"Country updated: ID {country.id}")
              return success_response("Country updated successfully", data=country.to_dict(), status_code=200)
          except IntegrityError as e: # Fallback for race conditions
              db.session.rollback()
              logger.warning(f"Integrity error updating country {country_id}: {e}")
              # Determine if it was name or code uniqueness based on error
              return error_response(f"Another country with the same name or code already exists", error="duplicate_entry_on_update", status_code=409)
          except Exception as e:
              db.session.rollback()
              logger.error(f"Error updating country {country_id}: {e}", exc_info=True)
              return error_response("Failed to update country", error=str(e), status_code=500)

      def delete_country(self, country_id):
          country = Country.query.get(country_id)
          if not country:
              return error_response("Country not found", error="not_found", status_code=404)

          # Crucial: Dependency Check for States
          if State.query.filter_by(country_id=country_id).first():
              return error_response(
                  f"Cannot delete country '{country.name}' as it has associated states. Please delete or reassign states first.",
                  error="dependency_exists",
                  status_code=409  # 409 Conflict is appropriate here
              )
          # Note: The model has cascade="all, delete-orphan" for states.
          # The check above provides a safer, more informative error before cascading.
          # If silent cascading deletion of states is the desired behavior, this check can be removed.

          try:
              country_name = country.name
              db.session.delete(country)
              db.session.commit()
              logger.info(f"Country deleted: ID {country_id}, Name '{country_name}'")
              # Service returns success; route handler will convert to 204 No Content
              return success_response("Country deleted successfully", status_code=200)
          except Exception as e:
              db.session.rollback()
              logger.error(f"Error deleting country {country_id}: {e}", exc_info=True)
              return error_response("Failed to delete country", error=str(e), status_code=500)
  ```

## 4. Route Layer (`src/app/routes/country_route.py`)

- **Create Blueprint and Import Services/Utils:**

  ```python
  from flask import Blueprint, request, jsonify
  from ..services.country_service import CountryService
  from ..utils.response import create_response
  from ..utils.decorators import jwt_required, role_required # Assuming role_required exists from decorators.py
  from ..utils.roles import UserRoles # Assuming UserRoles enum exists
  import logging

  logger = logging.getLogger(__name__)

  country_bp = Blueprint('countries', __name__, url_prefix='/api/v1/countries')
  country_service = CountryService()

  @country_bp.route('/', methods=['POST'])
  @jwt_required()
  @role_required(UserRoles.ADMIN) # Admin role required
  def create_country_route():
      data = request.get_json()
      if not data:
          return create_response(status="error", message="Request body must be JSON"), 400
      result = country_service.create_country(data)
      status_code = result.get('status_code', 500)
      return create_response(**result), status_code

  @country_bp.route('/', methods=['GET'])
  # Public endpoint (Guest, User, Seller, Admin allowed)
  def get_countries_route():
      args = request.args
      result = country_service.get_all_countries(args)
      status_code = result.get('status_code', 500)
      return create_response(**result), status_code

  @country_bp.route('/<int:country_id>', methods=['GET'])
  # Public endpoint
  def get_country_by_id_route(country_id):
      result = country_service.get_country_by_id(country_id)
      status_code = result.get('status_code', 500)
      return create_response(**result), status_code

  @country_bp.route('/<int:country_id>/states', methods=['GET'])
  # Public endpoint (assuming, adjust roles as needed)
  def get_states_by_country_route(country_id):
      args = request.args
      result = country_service.get_states_by_country(country_id, args)
      status_code = result.get('status_code', 500)
      return create_response(**result), status_code

  @country_bp.route('/<int:country_id>', methods=['PATCH']) # Typically PATCH for partial updates
  @jwt_required()
  @role_required(UserRoles.ADMIN) # Admin role required
  def update_country_route(country_id):
      data = request.get_json()
      if not data:
          return create_response(status="error", message="Request body must be JSON"), 400
      result = country_service.update_country(country_id, data)
      status_code = result.get('status_code', 500)
      return create_response(**result), status_code

  @country_bp.route('/<int:country_id>', methods=['DELETE'])
  @jwt_required()
  @role_required(UserRoles.ADMIN) # Admin role required
  def delete_country_route(country_id):
      result = country_service.delete_country(country_id)
      status_code = result.get('status_code', 500)
      if result.get('status') == 'success' and status_code == 200:
          return "", 204 # Return empty body with 204 status for successful deletion
      return create_response(**result), status_code

  # Register blueprint in app factory (e.g., in app/__init__.py)
  # from .routes.country_route import country_bp
  # app.register_blueprint(country_bp)
  ```

## 5. Key Considerations & Error Handling

- **Role-Based Access Control (RBAC):**
  - **Public Read:** Listing countries (`/`), getting a specific country (`/<id>`), and its states (`/<id>/states`) are public.
  - **Admin CUD:** Creating, updating, and deleting countries are restricted to Admin users.
- **Input Validation:**
  - Performed in `CountryService` via `validate_country_input`.
  - Ensures `name` is present, non-empty, and meets length requirements. `code` is optional but validated if present.
  - Returns 400 Bad Request for validation errors.
- **Normalization:**
  - Country names: `strip()` and `title()` case.
  - Country codes: `strip()` and `upper()` case.
- **Uniqueness Constraint:**
  - `name` and `code` fields are unique in the database.
  - Service methods include explicit, case-insensitive checks before database operations to provide 409 Conflict errors.
  - `IntegrityError` is caught during commit as a fallback.
- **Error Handling Strategy:**
  - Service Layer: Returns dictionaries with status, message, data, error details, and `status_code`.
  - Route Layer: Uses `create_response` to format the final JSON output with appropriate HTTP status codes from the service. Implements 204 No Content for successful deletions.
- **Relationship Management (Deletion):**
  - The `Country` model has `cascade="all, delete-orphan"` for its `states` relationship.
  - **Crucial:** `delete_country` service method includes an explicit check for linked `State` records and returns a `409 Conflict` if they exist. This is generally safer than silent cascading deletion. If cascading deletion is desired, this explicit check can be removed, but the API documentation must clearly state this behavior.
- **Pagination & Filtering:**
  - Implemented in `get_all_countries` (and `get_states_by_country`) using query parameters like `page`, `per_page`, `search`, `sort_by`, `order`.
- **Serialization (`to_dict()`):**
  - The `to_dict()` method on the `Country` model controls the API response structure. Ensure related models (like `State`) also have appropriate serialization methods.

By following these steps, you can implement robust and maintainable CRUD operations for the `Country` model, consistent with the application's overall architecture and best practices.
