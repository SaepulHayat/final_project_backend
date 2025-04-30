# src/app/views/seller_views.py

from flask import Blueprint, request, jsonify, g
# Assuming decorators are defined elsewhere
# from ..auth.decorators import login_required, role_admin, role_user, role_seller, roles_required
# Placeholder decorators for demonstration
def login_required(f): return f
def role_admin(f): return f
def role_user(f): return f
def role_seller(f): return f
def roles_required(*roles):
    def wrapper(f):
        return f
    return wrapper

# Import necessary models
from ..model.seller import Seller
from ..model.user import User # Needed for linking

# Create Blueprint
seller_bp = Blueprint('seller_bp', __name__, url_prefix='/api/v1/sellers')

# --- Seller Model Endpoints ---

# POST /api/v1/sellers/ (User - Authenticated)
@seller_bp.route('/', methods=['POST'])
@login_required
@role_user # Only regular users can *become* sellers initially
def create_seller_profile():
    """
    Create a seller profile for the current authenticated user.
    Accessible by: User (Authenticated)
    Links to User, potentially changes user role to 'Seller'.
    """
    # --- Implementation Placeholder ---
    # 1. Get current user ID from token/session (e.g., g.user.id).
    # 2. Check if user already has a seller profile. Return error if yes.
    # 3. Get seller profile data from request (name, location).
    # 4. Validate data.
    # 5. Create new Seller object, linking user_id.
    # 6. Optionally: Update User's role to 'Seller'.
    # 7. Add to database session and commit.
    # 8. Return created seller profile or success message.
    # --- End Implementation Placeholder ---
    # user_id = g.user.id # Example
    return jsonify({"message": "Create seller profile placeholder"}), 201

# GET /api/v1/sellers/ (Guest, User, Seller, Admin)
@seller_bp.route('/', methods=['GET'])
def list_sellers():
    """
    List all sellers (paginated). Public listing.
    Accessible by: Guest, User, Seller, Admin
    """
    # --- Implementation Placeholder ---
    # 1. Get pagination parameters from request args.
    # 2. Query database for sellers with pagination.
    # 3. Serialize seller data.
    # 4. Return paginated list.
    # --- End Implementation Placeholder ---
    return jsonify({"message": "List all sellers placeholder"}), 200

# GET /api/v1/sellers/me (Seller, Admin)
@seller_bp.route('/me', methods=['GET'])
@login_required
@roles_required('Seller', 'Admin')
def get_current_seller_profile():
    """
    Get the current user's seller profile.
    Accessible by: Seller, Admin
    """
    # --- Implementation Placeholder ---
    # 1. Get current user ID from token/session (e.g., g.user.id).
    # 2. Query database for the Seller profile linked to the user_id.
    # 3. Handle not found error (404 - maybe user is not a seller).
    # 4. Serialize seller data.
    # 5. Return seller profile.
    # --- End Implementation Placeholder ---
    # user_id = g.user.id # Example
    return jsonify({"message": "Get current seller profile placeholder"}), 200

# GET /api/v1/sellers/{seller_id} (Guest, User, Seller, Admin)
@seller_bp.route('/<int:seller_id>', methods=['GET'])
def get_seller_profile(seller_id):
    """
    Get a specific seller's profile. Public profile view.
    Accessible by: Guest, User, Seller, Admin
    """
    # --- Implementation Placeholder ---
    # 1. Query database for seller by seller_id.
    # 2. Handle not found error (404).
    # 3. Serialize seller data.
    # 4. Return seller profile.
    # --- End Implementation Placeholder ---
    return jsonify({"message": f"Get profile for seller {seller_id} placeholder"}), 200

# PATCH /api/v1/sellers/me (Seller)
@seller_bp.route('/me', methods=['PATCH'])
@login_required
@role_seller # Only sellers can update their own profile via /me
def update_current_seller_profile():
    """
    Update the current user's seller profile.
    Accessible by: Seller
    """
    # --- Implementation Placeholder ---
    # 1. Get current user ID from token/session (e.g., g.user.id).
    # 2. Get update data from request body (name, location).
    # 3. Validate data.
    # 4. Query database for the Seller profile linked to the user_id. Handle 404.
    # 5. Update seller object fields.
    # 6. Commit changes.
    # 7. Return updated seller profile or success message.
    # --- End Implementation Placeholder ---
    # user_id = g.user.id # Example
    return jsonify({"message": "Update current seller profile placeholder"}), 200

# PATCH /api/v1/sellers/{seller_id} (Admin)
@seller_bp.route('/<int:seller_id>', methods=['PATCH'])
@login_required
@role_admin
def update_seller_profile(seller_id):
    """
    Update any seller's profile.
    Accessible by: Admin
    """
    # --- Implementation Placeholder ---
    # 1. Get update data from request body.
    # 2. Validate data.
    # 3. Query database for seller by seller_id. Handle 404.
    # 4. Update seller object fields.
    # 5. Commit changes.
    # 6. Return updated seller profile or success message.
    # --- End Implementation Placeholder ---
    return jsonify({"message": f"Update profile for seller {seller_id} placeholder"}), 200

# DELETE /api/v1/sellers/{seller_id} (Admin)
@seller_bp.route('/<int:seller_id>', methods=['DELETE'])
@login_required
@role_admin
def delete_seller_profile(seller_id):
    """
    Delete a seller profile. Consider implications for associated books and user role.
    Accessible by: Admin
    """
    # --- Implementation Placeholder ---
    # 1. Query database for seller by seller_id. Handle 404.
    # 2. Consider consequences: What happens to their books? Reassign? Delete?
    # 3. Consider consequences: Revert User role from 'Seller' to 'User'?
    # 4. Perform deletion of Seller record.
    # 5. Perform related updates (User role, potentially Book ownership if applicable).
    # 6. Commit changes.
    # 7. Return success message.
    # --- End Implementation Placeholder ---
    return jsonify({"message": f"Delete seller profile {seller_id} placeholder"}), 200

