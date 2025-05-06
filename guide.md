# Geographic Models CRUD Plan

This section outlines CRUD operations for the normalized geographic models (Country, State, City) and the specific address model (Location).

## 1. Country Model (Country)

Base Path: `/api/v1/countries`

| Operation | HTTP Method | Endpoint        | Action                      | Allowed Roles              | Notes                                                   |
| --------- | ----------- | --------------- | --------------------------- | -------------------------- | ------------------------------------------------------- |
| Create    | POST        | `/`             | Create a new country.       | Admin                      | Requires unique name and potentially code.              |
| Read      | GET         | `/`             | List all countries.         | Guest, User, Seller, Admin | Useful for populating dropdowns. Consider pagination.   |
| Read      | GET         | `/{country_id}` | Get a specific country.     | Guest, User, Seller, Admin | Returns details based on the ID.                        |
| Update    | PATCH       | `/{country_id}` | Update a country's details. | Admin                      | Allows partial updates to name or code.                 |
| Delete    | DELETE      | `/{country_id}` | Delete a country.           | Admin                      | Caution: Check for existing linked State records first. |

## 2. State Model (State)

Base Path: `/api/v1/states`

| Operation | HTTP Method | Endpoint      | Action                    | Allowed Roles              | Notes                                                        |
| --------- | ----------- | ------------- | ------------------------- | -------------------------- | ------------------------------------------------------------ |
| Create    | POST        | `/`           | Create a new state.       | Admin                      | Requires name and a valid country_id.                        |
| Read      | GET         | `/`           | List all states.          | Guest, User, Seller, Admin | Allow filtering by country_id. Consider pagination.          |
| Read      | GET         | `/{state_id}` | Get a specific state.     | Guest, User, Seller, Admin | Returns details based on the ID.                             |
| Update    | PATCH       | `/{state_id}` | Update a state's details. | Admin                      | Allows partial updates to name. Changing country_id is rare. |
| Delete    | DELETE      | `/{state_id}` | Delete a state.           | Admin                      | Caution: Check for existing linked City records first.       |

## 3. City Model (City)

Base Path: `/api/v1/cities`

| Operation | HTTP Method | Endpoint     | Action                   | Allowed Roles              | Notes                                                      |
| --------- | ----------- | ------------ | ------------------------ | -------------------------- | ---------------------------------------------------------- |
| Create    | POST        | `/`          | Create a new city.       | Admin                      | Requires name and a valid state_id.                        |
| Read      | GET         | `/`          | List all cities.         | Guest, User, Seller, Admin | Allow filtering by state_id. Consider pagination.          |
| Read      | GET         | `/{city_id}` | Get a specific city.     | Guest, User, Seller, Admin | Returns details based on the ID.                           |
| Update    | PATCH       | `/{city_id}` | Update a city's details. | Admin                      | Allows partial updates to name. Changing state_id is rare. |
| Delete    | DELETE      | `/{city_id}` | Delete a city.           | Admin                      | Caution: Check for existing linked Location records first. |

## 4. Location Model (Location) - Specific Addresses

Base Path: `/api/v1/locations`

| Operation | HTTP Method | Endpoint         | Action                             | Allowed Roles          | Notes                                                                                                 |
| --------- | ----------- | ---------------- | ---------------------------------- | ---------------------- | ----------------------------------------------------------------------------------------------------- |
| Create    | POST        | `/`              | Create a new specific location.    | Admin                  | Requires address, zip_code, city_id. User-specific locations often created via User profile updates.  |
| Read      | GET         | `/`              | List all specific locations.       | Admin                  | Filterable by city_id. Listing all might have privacy implications depending on use case.             |
| Read      | GET         | `/{location_id}` | Get a specific location's details. | Admin, Associated User | 'Associated User' means the authenticated user whose user.location_id matches this location.id.       |
| Update    | PATCH       | `/{location_id}` | Update a location's details.       | Admin, Associated User | Users can only update their own associated location (address, zip_code, name). Admins can update any. |
| Delete    | DELETE      | `/{location_id}` | Delete a specific location.        | Admin                  | Caution: Check associated User records. May need to set user.location_id to NULL.                     |

## General Notes for Geographic/Location Models:

- **Authentication & Authorization:** Admin roles are required for most CUD operations on Country, State, City. Location CUD involves both Admins and potentially the associated User. Read operations on Country, State, City are generally public.
- **Data Validation:** Inputs for POST/PATCH require validation (e.g., existence of foreign keys like city_id, string formats).
- **Relationships:** Deleting parent records (Country, State, City) requires checking for dependent child records. Deleting a Location requires checking for associated Users.
- **User Location Management:** The CRUD for Location above assumes direct manipulation. In practice, creating/updating a User's location might be handled via `/api/v1/users/me/location` or similar endpoints that internally manage the Location record linked to the authenticated user.
- **Error Handling:** Use standard HTTP status codes.
