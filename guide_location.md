# Guide: Implementing Location CRUD Operations

This guide details how to implement Create, Read, Update, and Delete (CRUD) operations for the `Location` model, adhering to a layered architecture and incorporating best practices outlined in `guide_location.md`.

**Reference:**

- Location Model: `location.py`
- City Model (for relationship): `city.py`
- User Model (for relationship): `user.py`
- State Model: `state.py`
- Country Model: `country.py`
- Recommendations: `guide_location.md`

## 1. Model Layer (`src/app/model/location.py`)

- **Existing Model:** The Location model includes `id` (PK), `name` (String, nullable), `address` (String, nullable), `zip_code` (String, nullable), and `city_id` (FK to `cities.id`, non-nullable).
- **Relationships:**
  - Many-to-One with `City` (`city` backref).
  - One-to-Many with `User` (`users` backref, `lazy='select'`), linked via the nullable `User.location_id`.
- **Responsibilities:** Defines the data structure and database mapping for specific addresses or places.
- **Serialization:** The model already has a `to_dict()` method which includes city, state, and country names by traversing relationships. A `to_simple_dict()` is likely not needed for the `Location` model itself.

  ```python
  # Inside Location class in location.py

  def to_dict(self):
      """Returns a dictionary representation of the location, including city/state/country."""
      city_obj = self.city
      state_obj = city_obj.state if city_obj else None
      country_obj = state_obj.country if state_obj else None

      return {
          'id': self.id,
          'name': self.name,
          'address': self.address,
          'zip_code': self.zip_code,
          'city_id': self.city_id,
          'city_name': city_obj.name if city_obj else None,
          'state_name': state_obj.name if state_obj else None,
          'country_name': country_obj.name if country_obj else None,
      }
  ```

## 2. Utility Layer (`src/app/utils/`)

- **Validators (`validators.py`):**
  - Create a validation function: `validate_location_input(data, is_update=False)`.
  - Checks:
    - `city_id`: Required (unless `is_update`), must be an integer. (Existence check happens in the service layer).
    - `address`: Although nullable in the model, the API contract might require it for creation. Check if present (unless `is_update`), non-empty string, max length (e.g., 255).
    - `zip_code`: Optional. If present, check format/length (e.g., max 15) after normalization.
    - `name`: Optional. If present, check non-empty string, max length (e.g., 100) after normalization.
  - Return a dictionary of errors if validation fails, otherwise `None`.
- **Response Formatting (`response.py`):**
  - Utilize the existing `success_response`, `error_response`, and `create_response` functions for consistent API responses.
- **Decorators (`decorators.py`):**
  - Use `@jwt_required()` for endpoints requiring authentication (Create, Update, Delete, possibly Get by ID depending on authorization logic).
  - Use role-checking decorators like `@admin_required` from `decorators.py`.
  - Implement specific logic within routes/services for users accessing/modifying their _own_ location, as outlined in `guide_location.md`.

## 3. Service Layer (`src/app/services/location_service.py`)

- **Create `LocationService` Class:**

  ```python
  # Example Structure (adapt based on actual implementation)
  from ..model.location import Location
  from ..model.city import City
  from ..model.user import User # For dependency check
  from ..extensions import db
  from ..utils.validators import validate_location_input # Assuming this exists
  from ..utils.response import success_response, error_response
  from sqlalchemy.exc import IntegrityError
  import logging

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

  # Responsibilities: Encapsulates business logic for locations, validation,
  # database interaction, normalization, foreign key checks, dependency checks (users),
  # and specific error handling (e.g., 409 Conflict).
  ```

## 4. Route Layer (`src/app/routes/location_route.py`)

- **Create Blueprint and Import Services/Utils:**

  ```python
  from flask import Blueprint, request, jsonify
  from ..services.location_service import LocationService
  from ..utils.response import create_response # Use create_response
  from ..utils.decorators import jwt_required, admin_required # Import decorators
  from flask_jwt_extended import get_jwt_identity, get_jwt # To get user info for authorization
  from ..utils.roles import UserRoles # Assuming UserRoles enum exists
  import logging

  logger = logging.getLogger(__name__)

  location_bp = Blueprint('locations', __name__, url_prefix='/api/v1/locations')
  location_service = LocationService()

  @location_bp.route('/', methods=['POST'])
  @jwt_required()
  @admin_required # Only Admins can create locations directly via this endpoint
  def create_location_route():
      data = request.get_json()
      if not data:
          return create_response(status="error", message="Request body must be JSON"), 400

      result = location_service.create_location(data)
      status_code = result.get('status_code', 500)
      return create_response(**result), status_code

  @location_bp.route('/', methods=['GET'])
  @jwt_required() # Require login to list locations
  # Authorization logic is inside the service for this endpoint
  def get_locations_route():
      args = request.args # For pagination/filtering/searching
      # Need role to pass to service for authorization check
      jwt_data = get_jwt() # Get JWT payload
      user_role = jwt_data.get('role', None) # Assuming role is in JWT claims

      result = location_service.get_all_locations(args, user_role)
      status_code = result.get('status_code', 500)
      return create_response(**result), status_code

  @location_bp.route('/<int:location_id>', methods=['GET'])
  @jwt_required() # Require login to get a specific location
  # Authorization logic (Admin or Owner) is inside the service
  def get_location_by_id_route(location_id):
      current_user_id = get_jwt_identity() # Get user ID from JWT
      jwt_data = get_jwt() # Get JWT payload
      user_role = jwt_data.get('role', None) # Assuming role is in JWT claims

      result = location_service.get_location_by_id(location_id, current_user_id, user_role)
      status_code = result.get('status_code', 500)
      return create_response(**result), status_code

  @location_bp.route('/<int:location_id>', methods=['PATCH']) # Typically use PATCH for updates
  @jwt_required()
  # Authorization logic (Admin or Owner, with field restrictions) is inside the service
  def update_location_route(location_id):
      data = request.get_json()
      if not data:
          return create_response(status="error", message="Request body must be JSON"), 400

      current_user_id = get_jwt_identity() # Get user ID from JWT
      jwt_data = get_jwt() # Get JWT payload
      user_role = jwt_data.get('role', None) # Assuming role is in JWT claims

      result = location_service.update_location(location_id, data, current_user_id, user_role)
      status_code = result.get('status_code', 500)
      return create_response(**result), status_code

  @location_bp.route('/<int:location_id>', methods=['DELETE'])
  @jwt_required()
  @admin_required # Only Admins can delete locations
  def delete_location_route(location_id):
      result = location_service.delete_location(location_id)
      status_code = result.get('status_code', 500)

      # Handle 204 No Content for successful deletion
      if result.get('status') == 'success' and status_code == 200:
          return "", 204 # Return empty body with 204 status

      # Handle 409 Conflict if deletion blocked by dependency check
      if status_code == 409:
           return create_response(**result), status_code # Return the 409 response from service

      return create_response(**result), status_code

  # Register blueprint in app factory...
  # from .routes.location_route import location_bp
  # app.register_blueprint(location_bp)

  # Responsibilities: Defines API endpoints, handles HTTP requests/responses,
  # parses data, calls the LocationService, applies security decorators,
  # extracts user info from JWT for service-layer authorization, formats final JSON output.
  ```

## 5. Key Considerations & Error Handling

- **Role-Based Access Control (RBAC):**
  - **Admin:** Can Create, Read (all), Update (all fields), Delete locations.
  - **Authenticated User:** Can Read and Update _their own_ assigned location (potentially with field restrictions for updates, e.g., cannot change `city_id`). Listing all locations is restricted.
  - Use `@jwt_required` and `@admin_required` decorators, plus logic within service/route methods using `get_jwt_identity()` and JWT claims (`role`).
- **Input Validation:**
  - Performed in `LocationService` via `validate_location_input` (checking format, length, presence based on context).
  - Foreign key validation (`city_id` existence) is handled within the service methods (`create_location`, `update_location`).
  - Returns 400 Bad Request for validation errors, 404 Not Found if `city_id` doesn't exist.
- **Normalization:** Apply `strip()` and potentially `.title()`/`.capitalize()` to `name`, `address`, `zip_code` in the service layer before saving.
- **Dependency Management (Deletion):**
  - **Crucial:** The `delete_location` service method _must_ check if any `User` record references the location via `User.location_id`.
  - If a dependency exists, the deletion must be prevented, and a `409 Conflict` error should be returned. This prevents dangling references since `User.location_id` is nullable.
- **Error Handling Strategy:**
  - **Service Layer:** Returns dictionaries containing status, message, data/error details, and `status_code`. Handles specific errors like 404 Not Found, 409 Conflict, 403 Forbidden.
  - **Route Layer:** Unpacks the service dictionary using `create_response`. Handles basic request errors (e.g., non-JSON body). Implements the 204 No Content response for successful DELETE.
- **Pagination & Filtering:**
  - Implement in `get_all_locations` using `request.args` and SQLAlchemy's `paginate()` and filter methods.
- **Serialization (`to_dict()`):**
  - The `Location.to_dict()` method includes related city, state, and country information, providing a comprehensive representation in API responses.
