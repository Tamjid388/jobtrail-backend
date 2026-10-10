# What Changed: SQLite to Neon Postgres

This file is both a changelog for humans and an implementation prompt for an AI agent.
If you give this file to an agent, it should be able to re-apply the same fixes on the original broken repo.

> ## AGENT TASK (read this first)
>
> **Starting point:** Django 4.2 backend with SQLite (`db.sqlite3`), hardcoded `SECRET_KEY`, `DEBUG=True`, hardcoded `ALLOWED_HOSTS` / `CORS_ALLOWED_ORIGINS` in `config/settings.py`. No `DATABASE_URL`, no WhiteNoise, no `render.yaml` Blueprint (or an outdated one).
>
> **Goal state:** Neon Postgres only (no SQLite fallback), all secrets from env via `python-decouple`, `DATABASE_URL` parsed with `dj-database-url`, WhiteNoise for static files, `gunicorn` start command, working `render.yaml`, working `.env.example`.
>
> **Inputs you must ask the human for:** real `DATABASE_URL` (Neon Dashboard > Connect > Django, pooler host with `?sslmode=require&channel_binding=require`). Never invent it, never commit it.
>
> **Do NOT:**
> - Do NOT keep SQLite fallback. If `DATABASE_URL` is missing, the app must fail fast (this is intentional).
> - Do NOT hardcode `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `DATABASE_URL` in code.
> - Do NOT commit `.env`, `db.sqlite3`, `staticfiles/`, `venv/`.
> - Do NOT change app logic in `applications/` — only config/env/deploy files.
>
> **Verify at the end and report:** `pip install -r requirements.txt`, `python manage.py check`, `python manage.py migrate`, `python manage.py collectstatic --noinput` all pass. `GET /admin/login/` -> 200, `GET /api/applications/` -> 401 (means auth works, no crash).

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

## 3. File 1: `requirements.txt` (final state, 22 lines)

The 4 Postgres/production packages must be present at exactly these versions:

```
asgiref==3.11.1
certifi==2026.1.4
charset-normalizer==3.4.4
Django==4.2.7
django-cors-headers==4.3.1
django-filter==23.5
djangorestframework==3.14.0
djangorestframework-simplejwt==5.3.0
idna==3.11
pillow==12.3.0
PyJWT==2.14.0
python-decouple==3.8
pytz==2026.3.post1
requests==2.32.5
setuptools==80.9.0
sqlparse==0.5.5
tzdata==2026.1
urllib3==2.6.3
dj-database-url==2.1.0
psycopg2-binary==2.9.10
gunicorn==22.0.0
whitenoise==6.6.0
```

Simple meaning:
- `psycopg2-binary` = lets Django talk to Postgres.
- `dj-database-url` = converts the `DATABASE_URL` string into Django database settings.
- `python-decouple` was already there. It reads the `.env` file.
- `gunicorn` = production server for Render (we don't use `runserver` live).
- `whitenoise` = serves static files (admin CSS) on Render without extra setup.

Install with:
```bash
pip install -r requirements.txt
```

> Important: just having `requirements.txt` in the project does NOT mean the packages are installed. It is only a list.
> Every time someone adds a new package and you do `git pull`, run `pip install -r requirements.txt` again.
> It is safe to re-run — pip skips what you already have and installs only the new ones. Without this you will get `ModuleNotFoundError`.

## 4. File 2: `config/settings.py` (main change)

Apply all 5 sub-steps below. Search by anchor comment, replace the whole block.

### 4a. New imports at top

Old (anchor: `from pathlib import Path`):
```python
from pathlib import Path
```

New (exact replacement):
```python
from pathlib import Path

import dj_database_url
from decouple import config
```

Meaning: we now have tools to read `.env` and to understand Postgres URL.

### 4b. SECRET_KEY, DEBUG, ALLOWED_HOSTS now come from env

Old (may vary slightly in the broken repo — replace the whole hardcoded block):
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

New (exact replacement):
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

Old (anchor: `DATABASES = {` + `sqlite3`):
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

New (exact replacement, no fallback):
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

### 4d. Static files + WhiteNoise MIDDLEWARE (full block, copy-pasteable)

Target state — `MIDDLEWARE` must be exactly this (WhiteNoise right after SecurityMiddleware):
```python
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
```

And static config must be exactly this:
```python
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}
```

Meaning:
- On your laptop static files just work.
- On Render with `DEBUG=False`, Django stops serving static files. WhiteNoise does it for us.
- `collectstatic` collects admin CSS into `staticfiles/` folder during Render build.

### 4e. CORS: frontend URLs allowed

Old:
```python
CORS_ALLOWED_ORIGINS = [
    "https://ayan-jobtrail-frontend.vercel.app",
]
```

New (exact replacement):
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

## 5. File 3: `render.yaml` (Blueprint so Render knows how to build us)

Final file content must be exactly this:

```yaml
services:
  - type: web
    name: jobtrail-backend
    runtime: python
    plan: free
    buildCommand: "pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate"
    startCommand: "gunicorn config.wsgi:application --bind 0.0.0.0:$PORT"
    healthCheckPath: /admin/login/
    envVars:
      - key: PYTHON_VERSION
        value: 3.13.13
      - key: SECRET_KEY
        generateValue: true
      - key: DEBUG
        value: False
      - key: DATABASE_URL
        sync: false  # paste Neon URL in dashboard, never commit
      - key: ALLOWED_HOSTS
        value: localhost,127.0.0.1,.onrender.com
      - key: CORS_ALLOWED_ORIGINS
        value: http://localhost:5173,http://127.0.0.1:5173,https://ayan-jobtrail-frontend.vercel.app
```

## 6. File 4: `.env.example` (template, safe to commit)

This file has fake values. It tells new devs what to create.

```
SECRET_KEY=your-secret-key-here
DEBUG=True
DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DBNAME?sslmode=require&channel_binding=require
ALLOWED_HOSTS=localhost,127.0.0.1,.onrender.com,.vercel.app
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,https://ayan-jobtrail-frontend.vercel.app
```

## 7. File 5: `.env` (real secrets, never commit)

This file is on your laptop only. It is in `.gitignore` so Git will ignore it.

```
SECRET_KEY=django-insecure-pxu7#vjm8p44mlie33dh-mu!zjymr%to=djnw*rrak(_v9)ml3
DEBUG=True
DATABASE_URL=postgresql://neondb_owner:<PASSWORD>@ep-late-shape-b4xlh1m0-pooler.c-6.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,https://ayan-jobtrail-frontend.vercel.app
```

Note: password is hidden here. Use your real Neon password from Neon dashboard. Agent: ask the human for this value, do not invent it.

## 8. `.gitignore` check (agent must verify)

These lines must exist, otherwise `git status` will leak secrets:

```
.env
db.sqlite3
staticfiles/
venv/
__pycache__/
```

Do NOT push `.env` or `db.sqlite3` or `staticfiles/`.

## 9. How to run now (laptop)

```bash
cd jobtrail-backend
pip install -r requirements.txt
python manage.py check
python manage.py migrate
python manage.py runserver
```

- `migrate` will create tables inside Neon `neondb`, not local file.
- Open frontend at `http://localhost:5173`. Login should work without CORS error.

## 10. How to deploy (give this to the next person)

### Step 1. Push `jobtrail-backend/` folder as repo root

The new GitHub repo must have these files at top level (not inside a subfolder):

```
render.yaml
requirements.txt
manage.py
config/
applications/
.env.example
.gitignore
guide.md
```

How to do it (simple):

```bash
cd jobtrail-backend
git init
git add render.yaml requirements.txt manage.py config applications .env.example .gitignore guide.md README.md
git commit -m "Backend with Neon Postgres + Render blueprint"
git branch -M main
git remote add origin https://github.com/<YOUR-USERNAME>/<BACKEND-REPO>.git
git push -u origin main
```

Do NOT push `.env` or `db.sqlite3` or `staticfiles/`. They are already in `.gitignore`.

Check on GitHub: you should see `render.yaml` on the first page. If you see only `jobtrail-backend/` folder, you pushed the wrong level. Fix it.

### Step 2. Render > New > Blueprint > paste Neon DATABASE_URL

1. Go to Render Dashboard > New > Blueprint.
2. Pick the backend repo you just created.
3. Render reads `render.yaml` and shows env vars. Fill only this one manually:
   ```
   DATABASE_URL=postgresql://neondb_owner:<PASSWORD>@ep-late-shape-b4xlh1m0-pooler.c-6.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require
   ```
   Get it from Neon Dashboard > Connect > Django. Others (`SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`) come from `render.yaml` automatically.
4. Click Apply / Deploy.
5. Build runs: `pip install + collectstatic + migrate`. Watch logs for `Applying applications.0001_initial... OK`.
6. Test: open `https://<your-service>.onrender.com/admin/login/` — should show Django admin login (200). Open `https://<your-service>.onrender.com/api/applications/` — should say 401 (means auth works, no crash).

If build fails on `DATABASE_URL not found`, you forgot Step 2.3. Add it in Render > Environment > Add.

### Step 3. Update CORS + frontend URL after first deploy

Backend now lives at e.g. `https://jobtrail-backend-xyz.onrender.com`. Frontend must point there.

A. On Render backend > Environment, update:
```
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,https://ayan-jobtrail-frontend.vercel.app
```
Replace last URL with your real Vercel URL if different. Save — Render redeploys automatically.

B. On Vercel frontend (or frontend `.env`), set:
```
VITE_API_URL=https://jobtrail-backend-xyz.onrender.com/api
```
Note `/api` at end. Redeploy frontend.

C. Test full flow: open Vercel site > Register > Login > Add application > Refresh. No CORS error in browser console. If CORS error remains, the URL in `CORS_ALLOWED_ORIGINS` does not exactly match frontend URL (check `https://` vs `http://`, trailing slash).

Env recap for Render (5 vars):

```
SECRET_KEY=<auto-generated by Render, don't touch>
DEBUG=False
DATABASE_URL=<same Neon pooler URL>
ALLOWED_HOSTS=localhost,127.0.0.1,.onrender.com
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,https://ayan-jobtrail-frontend.vercel.app
```

## 11. Verification checklist (agent must run and report)

```bash
pip install -r requirements.txt
python manage.py check
python manage.py migrate
python manage.py collectstatic --noinput
```

- [ ] `check` passes with no errors
- [ ] `migrate` says `Applying applications.0001_initial... OK` (or `No migrations to apply` on re-run)
- [ ] `collectstatic` copies admin files to `staticfiles/` without error
- [ ] `runserver` starts, `/admin/login/` returns 200
- [ ] `/api/applications/` without token returns 401 (not 500)
- [ ] No `SECRET_KEY`, `DATABASE_URL`, or password appears in `git diff` / `git status`

## 12. Common mistakes for juniors

1. `backend won't start, error DATABASE_URL not found` -> you forgot to create `.env` file. Copy from `.env.example`.
2. `CORS error in browser` -> check `CORS_ALLOWED_ORIGINS` has your exact frontend URL with `http://` and port.
3. `password authentication failed` -> Neon password changed or `&channel_binding=require` missing. Copy fresh string from Neon > Connect > Django.
4. Never commit `.env`. Only `.env.example` goes to GitHub.
