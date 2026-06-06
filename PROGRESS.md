# DRF Universal Template — Bajarilgan ishlar

## Loyiha maqsadi

Har qanday Django REST Framework proyektga "tushib ketadigan" universal template yaratish.
Phone-based authentication, JWT rotation, audit logging, standart error format va swagger bilan.

---

## 1. O'rnatilgan package'lar

```
djangorestframework
djangorestframework-simplejwt
django-environ
drf-yasg
django-cors-headers
```

---

## 2. Papka tuzilmasi

```
TheGraduationWork/
├── apps/
│   ├── __init__.py
│   ├── common/
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py          # BaseModel, ActivityLog
│   │   ├── middleware.py      # CurrentUserMiddleware, RequestLogMiddleware
│   │   ├── pagination.py      # CustomPagination
│   │   ├── permissions.py     # IsOwner, IsActive, IsAdminOrReadOnly
│   │   ├── exceptions.py      # custom_exception_handler
│   │   ├── mixins.py          # LoggableMixin
│   │   └── migrations/
│   │       └── 0001_initial.py
│   └── users/
│       ├── __init__.py
│       ├── apps.py
│       ├── admin.py
│       ├── managers.py
│       ├── models.py
│       ├── serializers.py
│       ├── views.py
│       ├── urls.py
│       └── migrations/
│           └── 0001_initial.py
├── core/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── logs/                      # auto yaratiladi (gitignore ga qo'shilishi kerak)
│   ├── debug.log
│   └── error.log
├── .env                       # lokal, git ga kirmaydi
├── .env.example               # namuna, git ga kiradi
└── manage.py
```

---

## 3. apps/users — Custom User Model (phone-based)

### apps/users/managers.py
- `UserManager(BaseUserManager)` — `create_user(phone, password)` va `create_superuser` metodlari

### apps/users/models.py
```
User
  phone        — CharField, unique, USERNAME_FIELD
  full_name    — CharField, blank=True
  is_active    — BooleanField, default=True
  is_staff     — BooleanField, default=False
  created_at   — DateTimeField, auto_now_add
  updated_at   — DateTimeField, auto_now
```
> **Eslatma:** User BaseModel'dan meros olmaydi — AbstractBaseUser va BaseModel.save()
> orasida MRO konflikti bo'ladi. Barcha boshqa modellar BaseModel'dan meros oladi.

### apps/users/serializers.py
| Serializer | Vazifasi |
|---|---|
| `RegisterSerializer` | phone + full_name + password + password_confirm validatsiyasi |
| `UserSerializer` | foydalanuvchi ma'lumotlarini ko'rsatish/tahrirlash |
| `PhoneTokenObtainPairSerializer` | JWT tokenga phone va full_name ni qo'shadi |

### apps/users/views.py
| View | Vazifasi |
|---|---|
| `RegisterView` | Ro'yxatdan o'tish → user + access + refresh qaytaradi |
| `LoginView` | Kirish → access + refresh (phone + password) |
| `LogoutView` | Refresh tokenni blacklistga tushiradi |
| `MeView` | O'z profilini GET / PATCH qilish |

### apps/users/urls.py
```
POST   /api/users/register/
POST   /api/users/login/
POST   /api/users/logout/
POST   /api/users/token/refresh/
GET    /api/users/me/
PATCH  /api/users/me/
```

### apps/users/admin.py
- `UserAdmin` — list_display, search_fields, fieldsets to'liq sozlangan

---

## 4. apps/common — Shared components

### apps/common/models.py

#### BaseModel (abstract)
Barcha non-auth modellar shu dan meros oladi:
```
id          — UUIDField, primary_key=True, default=uuid4
created_at  — DateTimeField, auto_now_add
updated_at  — DateTimeField, auto_now
created_by  — FK(User, null=True, related_name='+')
updated_by  — FK(User, null=True, related_name='+')
is_active   — BooleanField, default=True
```
- `save()` — thread-local orqali `created_by` / `updated_by` ni avtomatik to'ldiradi
- `delete()` — soft delete: `is_active=False` qilib saqlaydi, o'chirmaydi
- `hard_delete()` — DB dan to'liq o'chirish kerak bo'lganda

#### ActivityLog
```
user        — FK(User, null=True)
action      — CharField, choices: create / update / delete
model_name  — CharField
object_id   — CharField
changes     — JSONField, null=True  →  {"field": {"old": "...", "new": "..."}}
ip_address  — GenericIPAddressField, null=True
created_at  — DateTimeField, auto_now_add
```

---

### apps/common/middleware.py

#### CurrentUserMiddleware
- Har bir request da `request.user` ni `threading.local()` ga saqlaydi
- `BaseModel.save()` shu thread-local'dan foydalanib `created_by`/`updated_by` ni to'ldiradi
- `get_current_user()` helper funksiya eksport qilinadi

#### RequestLogMiddleware
- Har bir HTTP requestni loglaydi
- Format: `method=POST path=/api/users/ status=201 user=5 ip=127.0.0.1 duration=12.4ms`

---

### apps/common/pagination.py — CustomPagination
```python
page_size            = 10
page_size_query_param = "page_size"
max_page_size        = 100
```
Response format:
```json
{
  "success": true,
  "count": 42,
  "next": "http://...",
  "previous": null,
  "results": [...]
}
```

---

### apps/common/permissions.py

| Klass | Qoida |
|---|---|
| `IsOwner` | `obj.created_by == request.user` bo'lsagina ruxsat |
| `IsActive` | `request.user.is_active == True` bo'lsagina ruxsat |
| `IsAdminOrReadOnly` | Admin — to'liq; boshqalar — faqat GET/HEAD/OPTIONS |

---

### apps/common/exceptions.py — custom_exception_handler
Barcha DRF xatolarini bir formatga keltiradi:
```json
{
  "success": false,
  "error": {
    "code": "validation_error",
    "message": "phone: This field may not be blank."
  }
}
```
- `ValidationError` uchun `validation_error` code
- Nested dict/list errorlarni rekursiv tekislaydi
- `settings.py` da `EXCEPTION_HANDLER` ga ulangan

---

### apps/common/mixins.py — LoggableMixin
`GenericAPIView` ga qo'shiladigan mixin:

| Method | Nima qiladi |
|---|---|
| `perform_create` | `created_by=request.user` + ActivityLog `create` yozadi |
| `perform_update` | `updated_by=request.user` + eski/yangi field'lar diff + ActivityLog `update` |
| `perform_destroy` | ActivityLog `delete` + `instance.delete()` (soft) |

IP olish: `HTTP_X_FORWARDED_FOR` → `REMOTE_ADDR` fallback

---

## 5. core/settings.py — To'liq sozlamalar

### Environment variables (.env orqali)
| Variable | Default | Nima |
|---|---|---|
| `SECRET_KEY` | — | Django secret key (majburiy) |
| `DEBUG` | `False` | Debug rejimi |
| `ALLOWED_HOSTS` | `*` | Ruxsat etilgan hostlar |
| `DATABASE_URL` | `sqlite:///db.sqlite3` | DB ulanish |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis URL |
| `JWT_ACCESS_DAYS` | `1` | Access token muddati (kun) |
| `JWT_REFRESH_DAYS` | `7` | Refresh token muddati (kun) |
| `CORS_ALLOW_ALL_ORIGINS` | `False` | CORS ochiq/yopiq |
| `CORS_ALLOWED_ORIGINS` | `[]` | Ruxsat etilgan originlar |

### JWT (SimpleJWT)
```python
ROTATE_REFRESH_TOKENS    = True   # har refresh'da yangi refresh token beriladi
BLACKLIST_AFTER_ROTATION = True   # eski refresh token ishlamay qoladi
UPDATE_LAST_LOGIN        = True
```

### Logging — RotatingFileHandler
```
logs/debug.log  — DEBUG va yuqori, 10MB × 5 ta backup
logs/error.log  — faqat ERROR va yuqori, 10MB × 5 ta backup
```

### DRF default sozlamalar
```python
DEFAULT_AUTHENTICATION_CLASSES → JWTAuthentication
DEFAULT_PERMISSION_CLASSES     → IsAuthenticated
DEFAULT_PAGINATION_CLASS       → CustomPagination
EXCEPTION_HANDLER              → custom_exception_handler
```

---

## 6. core/urls.py

```
POST  /api/users/register/
POST  /api/users/login/
POST  /api/users/logout/
POST  /api/users/token/refresh/   ← global SimpleJWT refresh
GET   /api/users/me/
GET   /swagger/                   ← Swagger UI
GET   /redoc/                     ← ReDoc
GET   /admin/
```

---

## 7. .env.example
```env
SECRET_KEY=django-insecure-change-this-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3
REDIS_URL=redis://localhost:6379/0
JWT_ACCESS_DAYS=1
JWT_REFRESH_DAYS=7
CORS_ALLOW_ALL_ORIGINS=True
```

---

## Qilinmagan (keyingi bosqich uchun)

- [ ] `settings/` bo'linmasi: `base.py`, `local.py`, `production.py`
- [ ] Docker + docker-compose (postgres, redis, app)
- [ ] Celery + Redis (async tasks)
- [ ] `pytest` + `factory_boy` test infrastrukturasi
- [ ] `Makefile` — tez buyruqlar
- [ ] Phone OTP (SMS orqali login)
- [ ] `pre-commit` hooks (black, flake8, isort)
