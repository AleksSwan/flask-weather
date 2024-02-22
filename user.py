from flask import Blueprint, jsonify, request
from sqlalchemy.exc import SQLAlchemyError  # Exception class for handling SQL errors
from sqlalchemy.future import select  # Modern way to create SQL SELECT statements

from database import SessionLocal, User

user_bp = Blueprint("user", __name__)


@user_bp.route("/users/", methods=["POST"])
async def create_user():
    # Parse request data
    data = request.get_json()
    username = data.get("username")
    balance = data.get("balance", 0)

    async with SessionLocal() as session:
        # Attempt to add a new user
        user = await User.add_user(username, balance, session)
        if not isinstance(user, User):
            return jsonify({"error": f"{user}"}), 500
        return (
            jsonify(
                {"id": user.id, "username": user.username, "balance": user.balance}
            ),
            201,
        )


@user_bp.route("/users/<int:user_id>", methods=["GET"])
async def fetch_user(user_id: int):
    async with SessionLocal() as session:
        # Attempt to fetch a user by ID
        user = await User.find_user_by_id(user_id, session)
        if not user:
            return jsonify({"error": "User not found"}), 404
        return (
            jsonify(
                {"id": user.id, "username": user.username, "balance": user.balance}
            ),
            200,
        )


@user_bp.route("/users/<int:user_id>", methods=["PUT"])
async def update_user(user_id: int):
    # Parse request data
    data = request.get_json()

    async with SessionLocal() as session:
        # Attempt to update user details
        user = await User.update_user(session, user_id, **data)
        if not isinstance(user, User):
            return jsonify({"error": user}), 404
        return jsonify({"message": "User updated successfully", "id": user.id}), 200


@user_bp.route("/users/<int:user_id>", methods=["DELETE"])
async def delete_user(user_id: int):
    async with SessionLocal() as session:
        # Attempt to delete a user
        message, code = await User.delete_user(session, user_id)
        if code == 200:
            return jsonify({"message": message}), code
        return jsonify({"error": message}), code


@user_bp.route("/users", methods=["GET"])
async def list_users():
    async with SessionLocal() as session:
        try:
            # Execute query to fetch all users
            result = await session.execute(select(User))
            users = result.scalars().all()
            # Serialize user data for JSON response
            users_list = [
                {"id": user.id, "username": user.username, "balance": user.balance}
                for user in users
            ]
            return jsonify(users_list), 200
        except SQLAlchemyError as e:
            # Handle database errors
            return jsonify({"error": f"{e}"}), 500
