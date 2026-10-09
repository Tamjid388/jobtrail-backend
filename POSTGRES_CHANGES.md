# What Changed: SQLite to Neon Postgres

This file explains in simple words what was changed to connect the backend to Neon Postgres. For junior devs.

## 1. The problem before

- `config/settings.py` had secret values written directly in code.
- Database was always SQLite (`db.sqlite3` file). No way to use Postgres.
- `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS` could not be changed without editing code.
- Frontend on `localhost:5173` was blocked by CORS. Only Vercel URL was allowed.

## 2. The idea now

- Real secret values live in a `.env` file (not uploaded to GitHub).
- `settings.py` reads from `.env`.
- Database comes from one string called `DATABASE_URL`.
- No SQLite fallback anymore. If `DATABASE_URL` is missing, backend will stop with an error. This is on purpose so we notice it fast.

Format of connection string:
```
DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DBNAME?sslmode=require&channel_binding=require
```

## 3. File 1: `requirements.txt` (2 new lines added)

Added 2 packages:

```
dj-database-url==2.1.0
psycopg2-binary==2.9.9
```

Simple meaning:
- `psycopg2-binary` = lets Django talk to Postgres.
- `dj-database-url` = converts the `DATABASE_URL` string into Django database settings.
- `python-decouple` was already there. It reads the `.env` file.

Install with:
```bash
pip install -r requirements.txt
```

## 4. File 2: `config/settings.py` (main change)

### 4a. New imports at top

Old:
```python
from pathlib import Path
```

New:
```python
from pathlib import Path

import dj_database_url
from decouple import config
```

Meaning: we now have tools to read `.env` and to understand Postgres URL.

### 4b. SECRET_KEY, DEBUG, ALLOWED_HOSTS now come from env

Old:
```python
SECRET_KEY = 'django-insecure-pxu7#vjm8p44mlie33dh-mu!zjymr%to=djnw*rrak(_v9)ml3'
DEBUG = True
ALLOWED_HOSTS = [
".onrender.com",
".vercel.app",
"localhost",
"127.0.0.1",
]
```

New:
```python
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = [h.strip() for h in config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',') if h.strip()]
```

Meaning:
- No secret in code anymore.
- `DEBUG=True` on your laptop, `DEBUG=False` on Render.
- `ALLOWED_HOSTS` is a comma list in `.env`, example: `localhost,127.0.0.1,.onrender.com`.

### 4c. Database: SQLite removed, Neon Postgres only

Old:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

New:
```python
DATABASES = {
    'default': dj_database_url.parse(
        config('DATABASE_URL'),
        conn_max_age=0,
        conn_health_checks=True,
        ssl_require=True,
    )
}
```

Meaning:
- `config('DATABASE_URL')` takes the Neon string from `.env`.
- `ssl_require=True` keeps Neon secure connection (`?sslmode=require`).
- `conn_max_age=0` is best for Neon pooler (we use `-pooler` host). It closes DB connection after each request, pooler handles the rest.
- No `db.sqlite3` anymore. All data goes to Neon `neondb`.

### 4d. CORS: frontend URLs allowed

Old:
```python
CORS_ALLOWED_ORIGINS = [
    "https://ayan-jobtrail-frontend.vercel.app",
]
```

New:
```python
CORS_ALLOWED_ORIGINS = [o.strip() for o in config('CORS_ALLOWED_ORIGINS', default='http://localhost:5173,http://127.0.0.1:5173').split(',') if o.strip()]
```

Meaning:
- Browser blocks frontend if backend does not allow it. This fixes that.
- In `.env` we set:
```
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,https://ayan-jobtrail-frontend.vercel.app
```
- Local dev uses `localhost:5173`, production uses Vercel URL. Both work now.

## 5. File 3: `.env.example` (template, safe to commit)

This file has fake values. It tells new devs what to create.

```
SECRET_KEY=your-secret-key-here
DEBUG=True
DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DBNAME?sslmode=require&channel_binding=require
ALLOWED_HOSTS=localhost,127.0.0.1,.onrender.com,.vercel.app
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,https://ayan-jobtrail-frontend.vercel.app
```

## 6. File 4: `.env` (real secrets, never commit)

This file is on your laptop only. It is in `.gitignore` so Git will ignore it.

```
SECRET_KEY=django-insecure-pxu7#vjm8p44mlie33dh-mu!zjymr%to=djnw*rrak(_v9)ml3
DEBUG=True
DATABASE_URL=postgresql://neondb_owner:<PASSWORD>@ep-late-shape-b4xlh1m0-pooler.c-6.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,https://ayan-jobtrail-frontend.vercel.app
```

Note: password is hidden here. Use your real Neon password from Neon dashboard.

## 7. How to run now (laptop)

```bash
cd jobtrail-backend
pip install -r requirements.txt
python manage.py check
python manage.py migrate
python manage.py runserver
```

- `migrate` will create tables inside Neon `neondb`, not local file.
- Open frontend at `http://localhost:5173`. Login should work without CORS error.

## 8. How to deploy (Render backend)

In Render dashboard > Environment, add these 5 vars:

```
SECRET_KEY=<new random secret, not laptop one>
DEBUG=False
DATABASE_URL=<same Neon pooler URL>
ALLOWED_HOSTS=localhost,127.0.0.1,.onrender.com
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,https://ayan-jobtrail-frontend.vercel.app
```

Then `migrate` once on Render.

## 9. Common mistakes for juniors

1. `backend won't start, error DATABASE_URL not found` -> you forgot to create `.env` file. Copy from `.env.example`.
2. `CORS error in browser` -> check `CORS_ALLOWED_ORIGINS` has your exact frontend URL with `http://` and port.
3. `password authentication failed` -> Neon password changed or `&channel_binding=require` missing. Copy fresh string from Neon > Connect > Django.
4. Never commit `.env`. Only `.env.example` goes to GitHub.
