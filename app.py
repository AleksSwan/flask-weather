import asyncio
import os
import random
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple

from aiohttp import ClientSession  # Asynchronous HTTP client/session
from asgiref.wsgi import WsgiToAsgi  # ASGI Adapter for using Uvicorn with Flask
from flask import Flask  # Flask for web app, jsonify for JSON responses
from flask import jsonify, request
from sqlalchemy import update
from sqlalchemy.exc import SQLAlchemyError  # Exception class for handling SQL errors

from database import Base, SessionLocal, User, engine
from user import user_bp

app = Flask(__name__)  # Initialize Flask app
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
asgi_app = WsgiToAsgi(app)  # wrap Flask app

# Cache dictionary to store temperature data with expiration times
temperature_cache: Dict[str, Dict[str, Any]] = {}
EXPIRATION_TIME: int = 600  # Cache expiration time in seconds

app.register_blueprint(user_bp)


# Async function to fetch weather data
async def fetch_weather(city: str) -> Optional[float]:
    current_time: datetime = datetime.now()  # Current time for cache expiration check
    if (
        city in temperature_cache
        and current_time <= temperature_cache[city]["expiration_time"]
    ):  # Check cache expiration
        temperature = temperature_cache[city]["temperature"]  # Get cached temperature
        return temperature
    async with ClientSession() as session:  # Start an async HTTP session
        API_URL = "http://api.openweathermap.org/data/2.5/weather"
        API_KEY = os.environ.get("API_KEY", "test")  # Get API key from environment
        params = {"q": city, "appid": API_KEY, "units": "metric"}
        async with session.get(
            API_URL, params=params
        ) as response:  # Send async GET request
            if response.status == 200:
                data = await response.json()  # Parse JSON response
                temperature = data.get("main", {}).get("temp")  # Extract temperature
                temperature_cache[city] = {
                    "temperature": temperature,
                    "expiration_time": current_time
                    + timedelta(seconds=EXPIRATION_TIME),  # Update cache
                }
                return temperature
            return None


async def update_user_balance(session, user_id: int, amount: float) -> Tuple[str, int]:
    """
    Updates the balance of a user with the specified amount.

    Args:
        session: The asynchronous session to use for database operations.
        user_id (int): The ID of the user to update.
        amount (float): The amount to add to the user's balance.

    Returns:
        Tuple[str, int]: A tuple containing a message describing the result
        of the operation and an HTTP status code.
    """
    try:
        # Construct the update statement
        stmt = (
            update(User).where(User.id == user_id).values(balance=User.balance + amount)
        )

        # Execute the update statement
        await session.execute(stmt)

        # Commit the transaction
        await session.commit()

        # Set the success message and status code
        message = "User balance updated"
        code = 200
    except SQLAlchemyError as e:
        # Rollback the transaction in case of error
        await session.rollback()

        # Set the error message and status code
        message = f"Error updating balance: {e}"
        code = 400

    return message, code


# Flask route to update user balance based on temperature
@app.route("/update-balance/<operation>/<int:user_id>/<city>", methods=["GET"])
async def update_balance(operation: str, user_id: int, city: str):
    async with SessionLocal() as session:  # Start a new database session
        user = await User.find_user_by_id(user_id, session)  # Find user by ID
        if not user:
            return jsonify({"error": "User not found"}), 404

        temperature = await fetch_weather(city)  # Fetch weather data
        if temperature is None:
            return (
                jsonify(
                    {
                        "error": f"Failed to fetch weather in {city.capitalize()}. Balance not changed"
                    }
                ),
                400,
            )

        if operation == "decrease":
            amount = -temperature  # Decrease balance by temperature
        else:
            amount = temperature  # Increase balance by temperature

        message = await user.update_balance(session, amount)  # Update user balance
        return jsonify({"message": message}), 200


@app.route("/update-balance", methods=["POST"])
async def update_balance_post():
    # Parse request data
    data = request.get_json()
    user_id = data.get("user_id")
    operation = data.get("operation")  # 'increase' or 'decrease'
    city = data.get("city")

    if operation not in ["increase", "decrease"]:
        return (
            jsonify(
                {"error": "Invalid operation specified. Use 'increase' or 'decrease'."}
            ),
            400,
        )

    async with SessionLocal() as session:  # Start a new database session
        temperature = await fetch_weather(city)  # Fetch weather data
        if temperature is None:
            return (
                jsonify(
                    {
                        "error": f"Failed to fetch weather in {city.capitalize()}. Balance not changed"
                    }
                ),
                400,
            )

        amount = (-temperature, temperature)[operation == "increase"]
        message, code = await update_user_balance(session, user_id, amount)
        return jsonify({"message": message}), code


# Async functions to initialize and seed the database
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)  # Drop all tables for a clean slate
        await conn.run_sync(Base.metadata.create_all)  # Create tables based on models


async def _seed_db_bulk():
    async with SessionLocal() as session:
        users = [
            User(username=f"User-{i}", balance=random.randint(5000, 15000))
            for i in range(1, 6)
        ]  # Create user instances
        session.add_all(users)  # Add users to session
        await session.commit()  # Commit the session to save users


async def seed_db():
    async with SessionLocal() as session:
        for i in range(1, 6):
            await User.add_user(
                username=f"User-{i}",
                balance=random.randint(5000, 15000),
                session=session,
            )  # Create user instance


# Main function to run database initialization, seeding, and start Flask app
def main():
    asyncio.run(init_db())  # Initialize database
    asyncio.run(seed_db())  # Seed database
    app.run(debug=True)  # Start Flask app


if __name__ == "__main__":
    main()
