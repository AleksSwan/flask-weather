# Async Flask Weather Application

This application is an asynchronous Flask web service designed to update user balances based on temperature data fetched from an external weather API. It leverages `asyncio`, `SQLAlchemy` (for async database operations), and `aiohttp` to perform asynchronous HTTP requests.

## Features

- Asynchronous database operations with SQLAlchemy.
- Asynchronous external API calls to fetch weather data.
- Update user balances based on real-time temperature data.
- Caching mechanism for temperature data to reduce API calls.

## Prerequisites

- Python 3.7+
- aiohttp
- Flask 2.0+
- SQLAlchemy 1.4+ with async support
- SQLite (or other SQLAlchemy-supported databases with async support)

## Installation

Clone the repository to your local machine:

```bash
git clone https://github.com/yourrepository/async-flask-weather-app.git
cd async-flask-weather-app
```

Create a virtual environment and activate it:

```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

Install the required packages:

```bash
pip install -r requirements.txt
```

## Configuration

Set the necessary environment variables:

```bash
export API_KEY='your_openweathermap_api_key_here'
```

Alternatively, you can modify the application code to directly include your API key or use a configuration file.

## Running the Application

Initialize and seed the database, then run the Flask application:

```bash
python -m app
```

The application will start on `http://localhost:5000`. Use the provided endpoints to interact with the application.

## API Endpoints

- `GET /update-balance/<operation>/<user_id>/<city>`: Update the user's balance based on the temperature in the specified city. `operation` can be `increase` or `decrease`.

## Development and Contribution

Contributions to this project are welcome! Please follow the standard fork, branch, and pull request workflow. Don't forget to update tests as necessary.

1. Fork the repository.
2. Create your feature branch (`git checkout -b feature/AmazingFeature`).
3. Commit your changes (`git commit -am 'Add some AmazingFeature'`).
4. Push to the branch (`git push origin feature/AmazingFeature`).
5. Open a pull request.

## License

Distributed under the MIT License. See `LICENSE` for more information.

