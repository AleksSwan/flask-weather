# Asynchronous Flask application

This application demonstrates an asynchronous Flask web service for managing user records and dynamically updating user balances based on real-time weather data. It leverages `asyncio` for asynchronous operations, `SQLAlchemy` for async database interactions, and `aiohttp` for fetching weather information.

## Features

- **Asynchronous Database Operations**: Utilizes SQLAlchemy with async/await syntax for non-blocking database interactions.
- **Dynamic Balance Updates**: Offers an endpoint to update user balances by either increasing or decreasing based on the current temperature of a specified city.
- **Weather Data Fetching**: Uses `aiohttp` to asynchronously fetch real-time weather data from an external API.
- **Caching mechanism**: Reduce the number of external API calls made to fetch current weather information.
- **User Management**: Supports adding, updating, deleting, and fetching user details asynchronously.

## Installation

Ensure you have Python 3.7+ installed, then follow these steps:

1. Clone the repository:
   ```sh
   git clone https://github.com/AleksSwan/flask-weather.git
   cd flask-weather
   ```

2. Create a virtual environment and activate it:

    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. Install required packages:
   ```sh
   pip install -r requirements.txt
   ```

## Configuration

Set the necessary environment variables:

```bash
export API_KEY='your_openweathermap_api_key_here'
```

## Usage

**SingleApp** Start the application:

```sh
python app.py
```

The application will run on `http://localhost:5000` by default.

**MultiApp** Execute the following command in the project root:

```sh
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app:asgi_app --bind 0.0.0.0:5000
```

This command runs the application with 4 worker processes, leveraging Uvicorn for async capabilities. Adjust the number of workers based on your server's specifications.

## Endpoints

### Update a user's balance based on the temperature in the specified city. `operation` can be `increase` or `decrease`.

- **POST /update-balance**:
  - Body: `{"user_id": 1, "operation": "increase", "city": "London"}`
- **GET /update-balance/\<operation\>/\<user_id\>/\<city\>**


### User managmment

- **GET /users**: List all users.
- **POST /users/**: Add a new user.
  - Body: `{"username": "john_doe", "balance": 1000}`
- **PUT /users/<user_id>**: Update an existing user.
  - Body: `{"username": "john_doe_updated", "balance": 1500}`
- **DELETE /users/<user_id>**: Delete a user by ID.
- **GET /users/<user_id>**: Fetch details of a specific user.

## Contributing

Contributions are welcome! Please fork the repository and submit pull requests with any enhancements. Ensure you follow the project's code style and add unit tests for any new features.

## License

Distributed under the MIT License. See `LICENSE` file for more information.
