iot_app
=======

Simple Django + Channels IoT ingestion backend.

Overview
--------
This project provides an HTTP + WebSocket backend for registering users, issuing JWTs, ingesting IoT telemetry and subscribing to real-time updates. It uses Django REST Framework for HTTP APIs and Django Channels (with Redis channel layer) for WebSocket messaging. Daphne is available to run the ASGI application.

Main features
-------------
- User registration and login (JWT token issuance).
- Protected endpoints (JWT-based) for user profile and device data retrieval.
- IoT data ingestion via HTTP POST and WebSocket ingestion endpoint.
- Real-time subscription to new IoT data via WebSocket groups (one group per user_id).

Prerequisites
-------------
- Python 3.11+ (project was developed against Django 6.0.3)
- PostgreSQL (server running and a database created)
- Redis (for Channels channel layer, default host localhost:6379)
- Recommended: virtualenv or venv

Dependencies
------------
See `requirements.txt`. Key packages:
- Django
- djangorestframework
- channels, channels_redis
- daphne
- psycopg2-binary
- python-decouple
- PyJWT

Configuration
-------------
The project expects environment variables (the repository includes a `.env` file in development). Example variables (from `.env`):

- DB_HOST (e.g. "localhost")
- DB_USER (Postgres username)
- DB_PASS (Postgres password)
- DB_PORT (e.g. 5432)
- DB_NAME (database name)
- SECRET_KEY (Django secret key)

Create a `.env` file at the project root (or set these variables in your shell). You can copy values from the included `.env` during local development.

Quick setup (development)
-------------------------
1. Create and activate a virtual environment:

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# or on Linux/macOS
# source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Ensure PostgreSQL and Redis are running and reachable with the credentials in your `.env`.

4. Run migrations(It will also create a default user):

````
{
    "username:"admin",
    "password":"password"
}
````
```bash
python manage.py migrate
```

5. Run the server

- For development you can run Django's runserver (ASGI application is configured):

```bash
python manage.py runserver
```

API endpoints (HTTP)
--------------------
This repo also contain iot_app.postman_collection.json. You can import it into your postman and test the API.

------------

Base path: http://localhost:8000/

- POST /auth/login/
  - Purpose: Login with credentials and receive a JWT token.
  - Request JSON: { "username": "<username>", "password": "<password>" }
  - Response: ````{ "message": "Successfully logged in", "token": "<jwt>" }````
  - Public endpoint (no token required).

- POST /users/
  - Purpose: Create a new user (registration).
  - Request JSON: { "name": "Name", "username": "email-or-username", "password": "secret" }
  - Response: created user's data (user_id generated).

- GET /users/
  - Purpose: List all users (requires authentication)

- GET /users/<user_id>/
  - Purpose: Get public details for a user by `user_id` (requires authentication)

- PUT /users/<user_id>/
  - Purpose: Update the authenticated user's profile (password change supported). Note: username cannot be changed.

- GET /profile/
  - Purpose: Return the authenticated user's profile (requires JWT token)

- POST /iot/data/
  - Purpose: Create a new IoT data record (HTTP ingestion).
  - Request JSON: { "user_id": "U0001", "metric_1": float, "metric_2": float, "metric_3": float (optional), "timestamp": "ISO8601" }
  - On success the server will broadcast a message to the user's WebSocket group: event NEW_DATA with the saved payload.
  - Requires authentication.

- GET /users/<user_id>/iot/latest/
  - Purpose: Get the latest IoT record for the given user.
  - Requires authentication.

- GET /users/<user_id>/iot/history/?limit=50&page=1
  - Purpose: Paginated historical IoT records for user. Defaults: limit=50, page=1.
  - Requires authentication.

Authentication
--------------
- JWT tokens are issued by `POST /auth/login/` using `user.jwt_utils.create_jwt_token`.
- The custom DRF authentication `user.authentication.JsonTokenAuthentication` expects the token in the HTTP header named `Token` (handled via Django request.META as `HTTP_TOKEN`).

Example header for protected endpoints:

```
Token: <JWT_TOKEN_HERE>
```

If the token is missing or invalid, the API will return an authentication failure.

WebSocket endpoints
-------------------
Two WebSocket endpoints are available (ASGI routing at `user.routing.websocket_urlpatterns`):

- ws://localhost/ws/ingest/
  - Purpose: WebSocket-based ingestion. The client must send a header named `token` with a valid JWT during the WS handshake. Messages should be JSON payloads matching the IotDataSerializer (same fields as POST /iot/data/).
  - On successful save the consumer responds with { "message": "Data saved successfully" } and broadcasts the NEW_DATA event to the user's group.

- ws://localhost/ws/subscribe/?user_id=U0001
  - Purpose: Subscribe to real-time NEW_DATA messages for a specific `user_id`. The client must send the `token` header with a valid JWT during the handshake and include query parameter `user_id`.
  - When new data for that user is saved (via HTTP or ws/ingest/) the server will push messages to the subscriber(s).

Example using `wscat` (install with npm install -g wscat) — subscribe:

```bash
wscat -c "ws://localhost:8000/ws/subscribe/?user_id=U0001" -H "token: <JWT>"
```

Example using `wscat` — ingest:

```bash
wscat -c "ws://localhost:8000/ws/ingest/" -H "token: <JWT>"
# then send a JSON line:
{"user_id":"U0001","metric_1":12.3,"metric_2":45.6,"timestamp":"2025-01-01T00:00:00Z"}
```

Models (summary)
----------------
- CustomUser
  - user_id (generated, unique, e.g. U0001)
  - name
  - username (unique)
  - password (hashed via Django make_password)
  - is_active
  - created_at, updated_at

- IotData
  - user_id (FK-like by validated user_id string; validated against CustomUser.user_id)
  - metric_1 (float, 0-100)
  - metric_2 (float, 0-200)
  - metric_3 (float, optional)
  - timestamp (datetime, must not be in the future according to current code)
  - created_at