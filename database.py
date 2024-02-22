from typing import Optional, Tuple, Union

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

SQLALCHEMY_DATABASE_URI = (
    "sqlite+aiosqlite:///./async_users.db"  # Database URI for async SQLite
)

# Create an asynchronous engine for SQLAlchemy
engine = create_async_engine(SQLALCHEMY_DATABASE_URI, echo=True)

# Create a sessionmaker for managing database sessions, bind it to the async engine
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


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
            return f"{e}"  # Return error message

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
            return f"{e}"

    # Async classmethod to delete a user
    @classmethod
    async def delete_user(cls, session: AsyncSession, user_id: int) -> Tuple[str, int]:
        try:
            result = await session.execute(
                select(User).filter_by(id=user_id)
            )  # Execute select query
            user = result.scalars().first()  # Get the first result
            if user:
                await session.delete(user)  # Delete the user
                await session.commit()  # Commit the session
                return "User deleted successfully", 200
            return "User not found", 404
        except SQLAlchemyError as e:
            await session.rollback()  # Rollback in case of error
            return f"{e}", 500

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
