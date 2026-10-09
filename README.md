# JobTrail — Job Application Tracker Backend

JobTrail is a job application tracking system that allows users to securely manage and track their job applications.

This repository contains the Django REST Framework backend API for the JobTrail application.

## Features

* JWT authentication
* User registration and login
* Application CRUD operations
* Owner-based application isolation
* Search applications by company or position
* Filter by application status and job type
* Ordering applications
* Pagination
* Application statistics
* Django Admin support

## Tech Stack

* Python 3.10+
* Django
* Django REST Framework
* SimpleJWT
* django-filter
* django-cors-headers
* SQLite
* python-decouple

## Project Structure

```text
jobtrail-backend/
├── applications/
│   ├── migrations/
│   ├── admin.py
│   ├── models.py
│   ├── serializers.py
│   ├── urls.py
│   └── views.py
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── .env
├── .env.example
├── .gitignore
├── manage.py
├── requirements.txt
└── README.md
```

## Installation

Clone the repository:

```bash
git clone <BACKEND_REPOSITORY_URL>
cd jobtrail-backend
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate the virtual environment on Windows:

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key
DEBUG=True
```

Do not commit the `.env` file to GitHub.

## Database Setup

Run migrations:

```bash
python manage.py migrate
```

Optional: create an admin user:

```bash
python manage.py createsuperuser
```

## Run the Server

```bash
python manage.py runserver
```

The API will be available at:

```text
http://127.0.0.1:8000/
```

## API Endpoints

### Authentication

```text
POST /api/register/
POST /api/login/
POST /api/token/refresh/
```

### Applications

```text
GET    /api/applications/
POST   /api/applications/
GET    /api/applications/<id>/
PATCH  /api/applications/<id>/
PUT    /api/applications/<id>/
DELETE /api/applications/<id>/
```

### Statistics

```text
GET /api/stats/
```

## Filtering, Search and Ordering

Filter by status:

```text
/api/applications/?status=INTERVIEW
```

Filter by job type:

```text
/api/applications/?job_type=REMOTE
```

Search:

```text
/api/applications/?search=frontend
```

Ordering:

```text
/api/applications/?ordering=-applied_on
```

Pagination:

```text
/api/applications/?page=2
```

Parameters can also be combined.

## Authentication

Protected endpoints require a JWT access token:

```text
Authorization: Bearer <access_token>
```

Each authenticated user can only access their own applications.

## Testing

Run Django system checks:

```bash
python manage.py check
```

The API was also tested using Postman for:

* Registration
* Login
* Token refresh
* CRUD
* Owner isolation
* Filtering
* Search
* Ordering
* Pagination
* Statistics
* Authentication errors

## Frontend Repository

The React frontend for this project is maintained in a separate repository:

```text
<FRONTEND_REPOSITORY_URL>
```

## License

This project is developed for educational and assignment purposes.
