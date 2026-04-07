# Task & Billing Manager API

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0.0-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Tests](https://img.shields.io/badge/Tests-Passing-brightgreen.svg)

A production-ready REST API for task management and payment processing via Paystack. Built with Flask, this SaaS-style backend demonstrates professional backend development practices including JWT authentication, database migrations, comprehensive testing, and API documentation.

## Features

- **User Authentication**: Secure JWT-based authentication with access and refresh tokens
- **Task Management**: Full CRUD operations with filtering, pagination, and statistics
- **Payment Processing**: Paystack integration for secure payment handling
- **API Documentation**: Auto-generated Swagger UI documentation
- **Database Flexibility**: SQLite for development, PostgreSQL for production
- **Comprehensive Testing**: pytest-based test suite with fixtures and mocks
- **Production Ready**: Render deployment configuration included

## Tech Stack

| Category | Technology |
|----------|------------|
| Framework | Flask 3.0, Flask-RESTful |
| Database | SQLAlchemy, Flask-Migrate |
| Auth | Flask-JWT-Extended, bcrypt |
| Payments | Paystack API |
| Docs | Flasgger (Swagger UI) |
| Testing | pytest, pytest-flask |
| Deployment | Gunicorn, Render |

## Local Setup

### Prerequisites

- Python 3.9+
- pip
- virtualenv (recommended)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/task-billing-api.git
cd task-billing-api
```

2. **Create and activate virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Initialize the database**
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

6. **Run the development server**
```bash
flask run
# or
python run.py
```

The API will be available at `http://localhost:5000`

## API Documentation

Interactive API documentation is available at `/api/docs` when the server is running.

### Endpoints Overview

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| **Authentication** ||||
| POST | `/api/auth/register` | No | Register a new user |
| POST | `/api/auth/login` | No | Login and get tokens |
| POST | `/api/auth/refresh` | Refresh | Refresh access token |
| GET | `/api/auth/me` | Yes | Get current user profile |
| PUT | `/api/auth/me` | Yes | Update user profile |
| POST | `/api/auth/logout` | Yes | Logout and blacklist token |
| **Tasks** ||||
| GET | `/api/tasks` | Yes | List all tasks (paginated) |
| POST | `/api/tasks` | Yes | Create a new task |
| GET | `/api/tasks/<id>` | Yes | Get a specific task |
| PUT | `/api/tasks/<id>` | Yes | Update a task |
| DELETE | `/api/tasks/<id>` | Yes | Cancel a task (soft delete) |
| GET | `/api/tasks/stats` | Yes | Get task statistics |
| **Payments** ||||
| POST | `/api/payments/initialize` | Yes | Initialize a payment |
| GET | `/api/payments/verify/<ref>` | Yes | Verify a payment |
| POST | `/api/payments/webhook` | No | Paystack webhook handler |
| GET | `/api/payments` | Yes | List all payments |
| GET | `/api/payments/<id>` | Yes | Get a specific payment |
| **Health** ||||
| GET | `/api/health` | No | API health check |

## Example Requests

### Register a New User

```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "kwame@example.com",
    "password": "securepass123",
    "full_name": "Kwame Mensah"
  }'
```

### Login

```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "kwame@example.com",
    "password": "securepass123"
  }'
```

### Get User Profile

```bash
curl -X GET http://localhost:5000/api/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Create a Task

```bash
curl -X POST http://localhost:5000/api/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "title": "Complete API documentation",
    "description": "Write comprehensive docs for all endpoints",
    "priority": "high",
    "due_date": "2025-12-31T23:59:59"
  }'
```

### List Tasks with Filters

```bash
curl -X GET "http://localhost:5000/api/tasks?status=pending&priority=high&page=1&per_page=10" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Update a Task

```bash
curl -X PUT http://localhost:5000/api/tasks/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "status": "in_progress",
    "priority": "medium"
  }'
```

### Delete (Cancel) a Task

```bash
curl -X DELETE http://localhost:5000/api/tasks/1 \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Get Task Statistics

```bash
curl -X GET http://localhost:5000/api/tasks/stats \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Initialize a Payment

```bash
curl -X POST http://localhost:5000/api/payments/initialize \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "amount": 100.50,
    "description": "Payment for project consultation",
    "currency": "GHS"
  }'
```

### Verify a Payment

```bash
curl -X GET http://localhost:5000/api/payments/verify/TASKBILL-ABC123DEF456 \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### List Payments

```bash
curl -X GET "http://localhost:5000/api/payments?status=success&page=1" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Refresh Access Token

```bash
curl -X POST http://localhost:5000/api/auth/refresh \
  -H "Authorization: Bearer YOUR_REFRESH_TOKEN"
```

### Logout

```bash
curl -X POST http://localhost:5000/api/auth/logout \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Paystack Test Credentials

For testing the payment integration, you'll need a Paystack account:

1. Sign up at [Paystack](https://paystack.com)
2. Get your test API keys from the dashboard
3. Add them to your `.env` file:
   ```
   PAYSTACK_SECRET_KEY=sk_test_your_secret_key
   PAYSTACK_PUBLIC_KEY=pk_test_your_public_key
   ```

**Note**: Always use test keys during development. Test transactions don't process real payments.

## Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_auth.py

# Run with coverage report
pytest --cov=app tests/
```

## Deployment to Render

### Prerequisites

- A [Render](https://render.com) account
- A [Paystack](https://paystack.com) account with API keys

### Steps

1. **Push your code to GitHub**

2. **Create a new Web Service on Render**
   - Connect your GitHub repository
   - Render will auto-detect the `render.yaml` configuration

3. **Configure Environment Variables**
   - `PAYSTACK_SECRET_KEY`: Your Paystack secret key
   - `PAYSTACK_PUBLIC_KEY`: Your Paystack public key
   - Other variables are auto-generated by Render

4. **Deploy**
   - Render will automatically build and deploy your application
   - Database migrations run automatically during build

### Manual Deployment

If not using `render.yaml`:

```bash
# Build command
pip install -r requirements.txt && flask db upgrade

# Start command
gunicorn run:app
```

## Live Demo

**API Base URL**: `https://your-app-name.onrender.com`

**Swagger Documentation**: `https://your-app-name.onrender.com/api/docs`

## Project Structure

```
task-billing-api/
├── app/
│   ├── __init__.py          # Application factory
│   ├── config.py             # Configuration classes
│   ├── extensions.py         # Flask extensions
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py           # User model
│   │   ├── task.py           # Task model
│   │   └── payment.py        # Payment model
│   ├── routes/
│   │   ├── __init__.py       # Blueprint registration
│   │   ├── auth.py           # Authentication endpoints
│   │   ├── tasks.py          # Task endpoints
│   │   └── payments.py       # Payment endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   └── paystack.py       # Paystack API service
│   └── utils/
│       ├── __init__.py
│       └── helpers.py        # Utility functions
├── tests/
│   ├── __init__.py
│   ├── conftest.py           # pytest fixtures
│   ├── test_auth.py          # Auth tests
│   ├── test_tasks.py         # Task tests
│   └── test_payments.py      # Payment tests
├── migrations/               # Database migrations
├── .env.example              # Environment template
├── .gitignore
├── requirements.txt
├── run.py                    # Application entry point
├── render.yaml               # Render deployment config
└── README.md
```

## Response Format

All API responses follow a consistent format:

**Success Response**
```json
{
  "success": true,
  "message": "Human readable message",
  "data": { ... },
  "meta": { "page": 1, "per_page": 10, "total": 50 }
}
```

**Error Response**
```json
{
  "success": false,
  "message": "Human readable error message",
  "errors": { "field": "specific error" }
}
```

## License

This project is licensed under the MIT License.

## Author

Built as a portfolio showcase project demonstrating professional Flask REST API development.

---

**Note**: This is a demonstration project. For production use, ensure proper security audits, rate limiting, and monitoring are implemented.
