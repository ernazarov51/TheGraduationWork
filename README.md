# DRF Template

Production-ready Django REST Framework starter template with phone-based JWT authentication, soft delete, activity logging, and standardised API responses.

---

## Features

- **Phone-based auth** — custom `User` model with `+998XXXXXXXXX` validation
- **JWT + rotation** — access / refresh tokens via SimpleJWT; refresh token blacklisted on every rotation and logout
- **BaseModel** — UUID primary key, `created_at / updated_at`, `created_by / updated_by` (auto-filled via middleware), soft delete
- **ActivityLog** — every create / update / delete action is recorded with field-level diff and IP address
- **Standardised responses** — all errors return `{"success": false, "error": {"code": "...", "message": "..."}}`
- **Throttling** — global anon/user limits + strict 5/min limit on the login endpoint
- **Filtering** — `django-filter` + `SearchFilter` + `OrderingFilter` wired up globally
- **Swagger / ReDoc** — auto-generated API docs at `/swagger/` and `/redoc/`
- **Health check** — `/api/health/` for Docker and load-balancer probes
- **Logging** — rotating file handlers (`debug.log` 10 MB × 5, `error.log` 10 MB × 5)
- **`create_admin` command** — create superuser from CLI without interactive prompts

---

## Tech Stack

| Package | Version |
|---|---|
| Django | 5.2 |
| djangorestframework | ≥ 3.15 |
| djangorestframework-simplejwt | ≥ 5.3 |
| django-environ | ≥ 0.11 |
| django-cors-headers | ≥ 4.3 |
| django-filter | ≥ 24.0 |
| drf-yasg | ≥ 1.21 |

---

## Project Structure

```
├── apps/
│   ├── common/                  # Shared infrastructure
│   │   ├── exceptions.py        # Custom exception handler
│   │   ├── middleware.py        # CurrentUserMiddleware, RequestLogMiddleware
│   │   ├── mixins.py            # LoggableMixin (ActivityLog on create/update/delete)
│   │   ├── models.py            # BaseModel, ActivityLog
│   │   ├── pagination.py        # CustomPagination (page_size=10, max=100)
│   │   ├── permissions.py       # IsOwner, IsActive, IsAdminOrReadOnly
│   │   ├── serializers.py       # BaseSerializer
│   │   ├── throttles.py         # LoginRateThrottle, BurstRateThrottle
│   │   ├── utils.py             # get_client_ip(), make_error(), make_success()
│   │   ├── validators.py        # validate_uzbek_phone()
│   │   └── views.py             # health_check
│   └── users/
│       ├── management/commands/
│       │   └── create_admin.py  # python manage.py create_admin
│       ├── admin.py
│       ├── managers.py          # UserManager (phone-based)
│       ├── models.py            # User model
│       ├── serializers.py
│       ├── urls.py
│       └── views.py
├── core/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── logs/                        # Auto-created; .gitkeep keeps folder in git
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── entrypoint.sh
├── manage.py
└── requirements.txt
```

---

## Quick Start

### 1. Use this template

Click **"Use this template"** on GitHub, or clone directly:

```bash
git clone https://github.com/your-username/drf-template.git my-project
cd my-project
```

### 2. Create virtual environment

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
```

Open `.env` and set at minimum:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
```

### 4. Run migrations and create admin

```bash
python manage.py migrate
python manage.py create_admin --phone +998901234567 --password YourPassword123
```

### 5. Start the server

```bash
python manage.py runserver
```

API docs → [http://127.0.0.1:8000/swagger/](http://127.0.0.1:8000/swagger/)

---

## Docker

### Start with Docker Compose

```bash
cp .env.example .env
# Edit .env: set DATABASE_URL=postgres://postgres:postgres@db:5432/drf_template

chmod +x entrypoint.sh          # only needed once after cloning

docker compose up --build
```

Services started:
- `app` → [http://localhost:8000](http://localhost:8000)
- `db` → PostgreSQL 16 on port 5432
- `redis` → Redis 7 on port 6379

`entrypoint.sh` automatically waits for the database, runs migrations, and collects static files before starting the app.

### Create admin inside Docker

```bash
docker compose exec app python manage.py create_admin \
  --phone +998901234567 --password Secret123!
```

### Production

In `docker-compose.yml`, swap the `command` line for gunicorn:
```yaml
command: gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 4
```
And uncomment `gunicorn` and `psycopg2-binary` in `requirements.txt`.

---

## API Endpoints

### Auth

| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| `POST` | `/api/v1/users/register/` | No | Register, returns access + refresh tokens |
| `POST` | `/api/v1/users/login/` | No | Login with phone + password (throttled: 5/min) |
| `POST` | `/api/v1/users/logout/` | Yes | Blacklist refresh token |
| `POST` | `/api/v1/token/refresh/` | No | Rotate refresh token |
| `GET` | `/api/v1/users/me/` | Yes | Get current user profile |
| `PATCH` | `/api/v1/users/me/` | Yes | Update current user profile |

### System

| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| `GET` | `/api/health/` | No | Database connectivity check |
| `GET` | `/swagger/` | No | Swagger UI |
| `GET` | `/redoc/` | No | ReDoc |

### Request / Response examples

**Register**
```json
POST /api/v1/users/register/
{
  "phone": "+998901234567",
  "full_name": "Ali Valiyev",
  "password": "Secret123!",
  "password_confirm": "Secret123!"
}
```
```json
{
  "user": { "id": 1, "phone": "+998901234567", "full_name": "Ali Valiyev", ... },
  "access": "<jwt-access-token>",
  "refresh": "<jwt-refresh-token>"
}
```

**Error format (all endpoints)**
```json
{
  "success": false,
  "error": {
    "code": "validation_error",
    "message": "phone: Enter a valid phone number in the format: +998XXXXXXXXX"
  }
}
```

---

## Environment Variables

| Variable | Default | Required | Description |
|---|---|---|---|
| `SECRET_KEY` | — | Yes | Django secret key |
| `DEBUG` | `False` | — | Debug mode |
| `ALLOWED_HOSTS` | `*` | — | Comma-separated allowed hosts |
| `DATABASE_URL` | `sqlite:///db.sqlite3` | — | Database connection URL |
| `REDIS_URL` | `redis://localhost:6379/0` | — | Redis URL (for Celery / cache) |
| `JWT_ACCESS_DAYS` | `1` | — | Access token lifetime in days |
| `JWT_REFRESH_DAYS` | `7` | — | Refresh token lifetime in days |
| `CORS_ALLOW_ALL_ORIGINS` | `False` | — | Open CORS for all origins |
| `CORS_ALLOWED_ORIGINS` | `[]` | — | Comma-separated allowed origins |

For S3 and Sentry variables see `.env.example`.

---

## Building on Top of This Template

### Adding a new app

```bash
python manage.py startapp products apps/products
```

Register it in `core/settings.py`:
```python
LOCAL_APPS = [
    "apps.common",
    "apps.users",
    "apps.products",   # add here
]
```

### Using BaseModel

Every new model should extend `BaseModel` to get UUID pk, timestamps, soft delete, and auto audit fields:

```python
from apps.common.models import BaseModel

class Product(BaseModel):
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
```

> `User` is the only model that does **not** extend `BaseModel` — `AbstractBaseUser`
> conflicts with BaseModel's `save()` and UUID primary key. User has its own
> `created_at / updated_at` fields instead.

### Using LoggableMixin

Add `LoggableMixin` to any `ModelViewSet` to get automatic ActivityLog entries:

```python
from apps.common.mixins import LoggableMixin

class ProductViewSet(LoggableMixin, viewsets.ModelViewSet):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
```

### Using BaseSerializer

```python
from apps.common.serializers import BaseSerializer

class ProductSerializer(BaseSerializer):
    class Meta:
        model = Product
        fields = ("id", "name", "price", "created_at")
        # is_active, created_by, updated_by are hidden automatically
```

### Using helpers

```python
from apps.common.utils import make_error, make_success

# In any view:
return make_error("out_of_stock", "This product is currently unavailable.", 400)
return make_success({"order_id": 42}, 201)
```

### Using permissions

```python
from apps.common.permissions import IsOwner, IsAdminOrReadOnly

class ProductDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsOwner]         # only the creator can edit
    # or
    permission_classes = [IsAdminOrReadOnly]  # admins write, others read
```

---

## Optional Integrations

All optional dependencies are pre-configured in `settings.py` — just uncomment and install.

| Integration | Package | Env var to set |
|---|---|---|
| PostgreSQL | `psycopg2-binary` | `DATABASE_URL=postgres://...` |
| S3 storage | `django-storages boto3` | `USE_S3=True` + AWS vars |
| Sentry | `sentry-sdk` | `SENTRY_DSN=https://...` |
| Celery | `celery redis` | `REDIS_URL=redis://...` |

---

## License

MIT
