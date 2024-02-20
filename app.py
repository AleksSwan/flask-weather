import asyncio
import os
import random
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union

from aiohttp import ClientSession  # Asynchronous HTTP client/session
from flask import Flask  # Flask for web app, jsonify for JSON responses
from flask import jsonify
from sqlalchemy import Float  # SQLAlchemy ORM model field types
from sqlalchemy import Column, Integer, String
from sqlalchemy.exc import SQLAlchemyError  # Exception class for handling SQL errors
from sqlalchemy.ext.asyncio import (  # Async SQLAlchemy components
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.future import select  # Modern way to create SQL SELECT statements
from sqlalchemy.orm import (
    DeclarativeBase,
)  # Base class for declarative SQLAlchemy models

app = Flask(__name__)  # Initialize Flask app
app.config["SQLALCHEMY_DATABASE_URI"] = (
    "sqlite+aiosqlite:///./async_users.db"  # Database URI for async SQLite
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Create an asynchronous engine for SQLAlchemy
engine = create_async_engine(app.config["SQLALCHEMY_DATABASE_URI"], echo=True)

# Create a sessionmaker for managing database sessions, bind it to the async engine
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Cache dictionary to store temperature data with expiration times
temperature_cache: Dict[str, Dict[str, Any]] = {}
EXPIRATION_TIME: int = 600  # Cache expiration time in seconds


class Base(DeclarativeBase):
    pass


# User model
class User(Base):
    __tablename__ = "users"  # Table name in database
    id = Column(Integer, primary_key=True)  # Primary key column
    username = Column(String(50), unique=True, nullable=False)  # Username column
    balance = Column(Float, nullable=False)  # Balance column

    # Async classmethod to add a new user to the database
    @classmethod
    async def add_user(
        cls, username: str, balance: int, session: AsyncSession
    ) -> Union["User", str]:
        try:
            new_user = cls(
                username=username, balance=balance
            )  # Create new User instance
            session.add(new_user)  # Add new user to the session
            await session.commit()  # Commit the session to save the user
            return new_user
        except SQLAlchemyError as e:
            await session.rollback()  # Rollback the session in case of error
            return f"Error adding user: {e}"  # Return error message

    # Async classmethod to find a user by ID
    @classmethod
    async def find_user_by_id(
        cls, user_id: int, session: AsyncSession
    ) -> Optional["User"]:
        try:
            result = await session.execute(
                select(User).filter_by(id=user_id)
            )  # Execute select query
            user = result.scalars().first()  # Get the first result
            return user
        except SQLAlchemyError:
            return None  # Return None if there's an error

    # Async classmethod to update a user
    @classmethod
    async def update_user(
        cls, session: AsyncSession, user_id: int, **kwargs
    ) -> Union["User", str]:
        try:
            result = await session.execute(
                select(User).filter_by(id=user_id)
            )  # Execute select query
            user = result.scalars().first()  # Get the first result
            if user:
                for key, value in kwargs.items():
                    if hasattr(user, key):  # Check if the user has the attribute
                        setattr(user, key, value)  # Set the attribute
                await session.commit()  # Commit the session to save changes
                return user
            return "User not found"
        except SQLAlchemyError as e:
            await session.rollback()  # Rollback in case of error
            return f"Error updating user: {e}"

    # Async classmethod to delete a user
    @classmethod
    async def delete_user(cls, session: AsyncSession, user_id: int) -> str:
        try:
            result = await session.execute(
                select(User).filter_by(id=user_id)
            )  # Execute select query
            user = result.scalars().first()  # Get the first result
            if user:
                await session.delete(user)  # Delete the user
                await session.commit()  # Commit the session
                return "User deleted successfully"
            return "User not found"
        except SQLAlchemyError as e:
            await session.rollback()  # Rollback in case of error
            return f"Error deleting user: {e}"

    # Instance method to update a user's balance
    async def update_balance(self, session: AsyncSession, amount: float) -> str:
        try:
            if self.balance + amount < 0:
                self.balance = 0.0  # Prevent negative balance
            else:
                self.balance += amount  # Update balance
            await session.commit()  # Commit the changes
            return f"User {self.username} balance updated successfully by {amount} to {self.balance:.2f}"
        except SQLAlchemyError as e:
            await session.rollback()  # Rollback in case of error
            return f"Error updating balance: {e}"


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
            delta = -temperature  # Decrease balance by temperature
        else:
            delta = temperature  # Increase balance by temperature

        if temperature:
            message = await user.update_balance(session, delta)  # Update user balance
            return jsonify({"message": message}), 200
        else:
            return (
                jsonify(
                    {"message": "Failed to fetch temperature. Balance not changed"}
                ),
                400,
            )


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
