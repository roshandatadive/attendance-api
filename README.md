# Attendance API

A production-ready FastAPI-based attendance management system with robust error handling, secure authentication, and comprehensive database integration.

## Overview

The Attendance API provides a complete solution for managing student attendance across educational institutions and programs. Built with FastAPI for high performance and PostgreSQL for reliability, the system offers:

- **Secure Authentication**: JWT-based token authentication with bcrypt password hashing
- **Robust Error Handling**: Comprehensive exception handlers with safe JSON serialization
- **RESTful Endpoints**: Clean API design supporting batch management, session tracking, and attendance recording
- **Role-Based Access Control**: Support for students, instructors, and monitoring officers
- **Production Deployment**: Configured for Render with environment-based settings

## Features

### Authentication & Security
- User signup and login with email/password validation
- JWT access tokens with configurable expiration
- Support for both JSON and form-data input formats
- Secure password hashing using bcrypt

### Attendance Management
- Create and manage batch groups
- Schedule attendance sessions with specific dates
- Record student attendance with status tracking
- View attendance history and analytics

### API Endpoints

#### Authentication
- `POST /auth/signup` - Create new user account
- `POST /auth/login` - Authenticate and receive JWT token

#### Batch Management
- `GET/POST /batches` - List and create batches
- `GET /batches/{id}` - View batch details
- `POST /batches/{id}/invite` - Generate batch invite token
- `POST /batches/join` - Join batch using token

#### Sessions
- `GET/POST /sessions` - Manage attendance sessions
- `GET /sessions/{id}` - View session details

#### Attendance
- `GET/POST /attendance` - Record and view attendance
- `GET /attendance/student/{student_id}` - Student attendance history

#### Monitoring
- `POST /monitoring/token` - Generate monitoring token with API key
- `GET /monitoring/stats` - View system statistics

## Technical Stack

- **Framework**: FastAPI 0.104+
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: PyJWT + bcrypt
- **Server**: Uvicorn
- **Testing**: pytest + httpx
- **Deployment**: Render

## Installation

### Prerequisites
- Python 3.10+
- PostgreSQL database
- pip or conda

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/roshandatadive/attendance-api.git
   cd attendance-api
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials and settings
   ```

5. **Initialize database**
   ```bash
   python -c "from app.db import init_db; init_db()"
   ```

6. **Run development server**
   ```bash
   uvicorn app.main:app --reload
   ```

API will be available at `http://localhost:8000`
API documentation: `http://localhost:8000/docs`

## Configuration

Environment variables (see `.env.example`):

```env
# Database
DATABASE_URL=postgresql://user:password@localhost/attendance_db

# JWT Settings
SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALGORITHM=HS256

# Security
BCRYPT_ROUNDS=12
MONITORING_API_KEY=secure-api-key

# Application
APP_NAME=Attendance API
```

## Error Handling

All errors return consistent JSON format:

```json
{
  "message": "Error type",
  "detail": "Detailed error information"
}
```

Common status codes:
- `200 OK` - Successful request
- `201 Created` - Resource created
- `400 Bad Request` - Invalid input
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_auth.py -v
```

## Deployment

### Render Deployment

1. Connect GitHub repository to Render
2. Create PostgreSQL database on Render
3. Set environment variables in Render dashboard
4. Deploy from `main` branch (uses `render.yaml` configuration)

### Production Checklist

- [ ] Set strong `SECRET_KEY` in environment
- [ ] Configure PostgreSQL with proper backups
- [ ] Enable HTTPS
- [ ] Set `DEBUG=false`
- [ ] Configure CORS for your frontend domain
- [ ] Review and test all endpoints
- [ ] Monitor logs and performance
- [ ] Regular database backups

## Code Structure

```
attendance-api/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI application setup
│   ├── config.py         # Environment configuration
│   ├── db.py             # Database connection
│   ├── errors.py         # Global exception handlers
│   ├── models.py         # SQLAlchemy ORM models
│   ├── schemas.py        # Pydantic request/response models
│   ├── security.py       # Authentication & authorization
│   └── routers/
│       ├── auth.py       # Authentication endpoints
│       ├── batches.py    # Batch management
│       ├── sessions.py   # Session management
│       ├── attendance.py # Attendance tracking
│       ├── institutions.py
│       ├── programme.py
│       └── monitoring.py
├── tests/                # Test suite
├── scripts/              # Utility scripts
├── requirements.txt      # Python dependencies
├── render.yaml           # Render deployment config
├── .env.example          # Environment variables template
└── README.md             # This file
```

## Key Implementation Details

### Error Handling
The system uses custom exception handlers that safely serialize all data types, including bytes, preventing JSON serialization errors. Validation errors return proper 422 responses instead of 500 server errors.

### Login Flexibility
The `/auth/login` endpoint accepts both JSON and form-data inputs, providing flexibility for different client implementations while maintaining validation and security.

### Authentication Flow
1. User registers with email, name, and password
2. Password is hashed with bcrypt (12 rounds)
3. User logs in to receive JWT access token
4. Token included in `Authorization: Bearer <token>` header
5. Protected endpoints verify token validity and user role

## Performance Considerations

- Connection pooling for database queries
- Efficient JWT token validation
- Indexed database columns for common queries
- Response compression with gzip
- Minimal dependencies for fast startup

## Security

- Passwords hashed with bcrypt (configurable rounds)
- JWT tokens with expiration
- Role-based access control
- CORS configuration
- Environment-based secrets management
- Input validation with Pydantic
- SQL injection prevention via ORM

## Contributing

For issues or suggestions, please contact the author (see CONTACT.txt).

## License

This project is provided as-is for educational and professional use.

---

**Author**: Roshan Sah  
**Last Updated**: May 2026  
**Status**: Production-Ready
