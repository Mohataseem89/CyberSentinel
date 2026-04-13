from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from database import create_user, get_user_by_username
from models import Session, User
import re

auth_bp = Blueprint('auth', __name__)

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    return True, ""

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()

        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')

        if not username or not email or not password:
            return jsonify({'error': 'All fields are required'}), 400

        if len(username) < 3:
            return jsonify({'error': 'Username must be at least 3 characters'}), 400

        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400

        is_valid, message = validate_password(password)
        if not is_valid:
            return jsonify({'error': message}), 400

        session = Session()
        existing_user = session.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        session.close()

        if existing_user:
            if existing_user.username == username:
                return jsonify({'error': 'Username already taken'}), 400
            return jsonify({'error': 'Email already registered'}), 400

        user_data = create_user(username, email, password)

        access_token = create_access_token(
            identity=str(user_data['id']),
            additional_claims={"role": user_data.get("role", "user")}
        )

        return jsonify({
            'message': 'User registered successfully',
            'user': user_data,
            'access_token': access_token
        }), 201

    except Exception as e:
        print(f"Registration error: {e}")
        return jsonify({'error': 'Registration failed'}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()

        username = data.get('username', '').strip()
        password = data.get('password', '')

        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400

        user = get_user_by_username(username)

        if not user or not user.check_password(password):
            return jsonify({'error': 'Invalid username or password'}), 401

        if not user.is_active:
            return jsonify({'error': 'Account is disabled'}), 403

        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={"role": user.role}
        )

        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict(),
            'access_token': access_token
        }), 200

    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'error': 'Login failed'}), 500


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    try:
        user_id = int(get_jwt_identity())

        session = Session()
        user = session.query(User).filter_by(id=user_id).first()
        session.close()

        if not user:
            return jsonify({'error': 'User not found'}), 404

        return jsonify({'user': user.to_dict()}), 200

    except Exception as e:
        print(f"Get user error: {e}")
        return jsonify({'error': 'Failed to get user'}), 500


@auth_bp.route('/check', methods=['GET'])
@jwt_required()
def check_auth():
    try:
        user_id = int(get_jwt_identity())

        session = Session()
        user = session.query(User).filter_by(id=user_id).first()
        session.close()

        if not user:
            return jsonify({'authenticated': False}), 401

        return jsonify({
            'authenticated': True,
            'user_id': user.id,
            'role': user.role
        }), 200

    except Exception:
        return jsonify({'authenticated': False}), 401