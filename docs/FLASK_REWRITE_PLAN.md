## Flask Rewrite Plan

### Target Architecture
- App factory pattern: `create_app(config_name)`
- Blueprints:
  - `auth` (teacher/admin), `observer_auth` (observer), `public`, `sessions`, `media`, `posts`, `students`, `admin`, `observer`
- Extensions: SQLAlchemy, Alembic, Flask-Login, Flask-WTF (CSRF), Celery or RQ, Logging
- Config: `config.py` with `Development/Testing/Production`; `.env`

### Proposed Project Layout
```
app/
  __init__.py
  config.py
  extensions.py
  models.py
  blueprints/
    auth/ routes.py forms.py
    observer_auth/ routes.py forms.py
    public/ routes.py
    sessions/ routes.py forms.py service.py
    media/ routes.py forms.py service.py storage.py
    posts/ routes.py forms.py service.py
    students/ routes.py service.py export.py
    admin/ routes.py forms.py
    observer/ routes.py
  tasks/ jobs.py
  templates/ ...
  static/ ...
migrations/
tests/
wsgi.py
```

### Model Mapping (Django → SQLAlchemy)
- User (Teacher/Admin) ← `CustomAdmin` (keep fields: username, email, password_hash, school, district_id, first_name, last_name, media_password?, profile_picture?)
- `Observer`: name, email(unique), password_hash, district_id, is_active, created_by_id, created_at
- `District`: name(unique), code(unique), is_active, created_at
- `Session`: name, original_name?, session_code(unique, len=8), section, module in {'2','4'}, created_at, is_paused, is_archived, archived_at, created_by_id, character_set
- `Student`: name, pin_hash (or strongly consider one-way hash), section_id, admin_id, device_id?, character_description?, avatar_image_path
- `Media`: session_id, title, description?, media_type, video_file?, image_file?, uploaded_at, graph_likes, eye_likes, read_likes, graph_tag?, is_graph, variable_tag?, submitted_password?, student_id?, posted_by_admin_id?, project_group?, project_images(json)?, is_project
- `StudentMediaInteraction`: student_id, media_id, liked_graph, liked_eye, liked_read, comment_count, created_at, updated_at, unique(student_id, media_id)
- `Comment`: media_id, parent_id(self), text, created_at, updated_at, name, device_id?, is_admin, student_id?, admin_avatar?

Indexes/Constraints
- Media: (session_id, uploaded_at desc), media_type, graph_tag, variable_tag
- Session: (created_by_id, section, is_archived=false) functional uniqueness enforced in code and DB with partial index where supported; else code-level
- StudentMediaInteraction: unique(student_id, media_id)

### Blueprints and Routes
- Auth (teacher/admin)
  - GET/POST `/teacher/login`, POST `/teacher/logout`
- Observer auth
  - GET/POST `/observer/login`, POST `/observer/logout`
- Public
  - GET `/`
- Sessions
  - GET/POST `/sessions/start`
  - GET `/sessions/<session_id>` (filters: graph_tag, variable_tag, pagination)
  - POST `/sessions/<session_id>/(archive|unarchive|pause|delete)`
  - GET `/sessions/check-availability?section=H`
- Media
  - GET/POST `/sessions/<session_id>/media/upload`
  - GET/POST `/media/<media_id>/edit`
  - POST `/media/<media_id>/delete`
  - POST `/media/<media_id>/react/<badge_type>`
  - GET/POST `/sessions/<session_id>/project/upload`
- Posts
  - GET `/post/<media_id>`
  - POST `/post/<media_id>/comment`
- Students
  - GET `/students/<student_id>`
  - POST `/students/<student_id>/delete`
  - GET `/students/export`
  - POST `/students/generate`
- Admin
  - GET `/admin/dashboard`
  - POST `/admin/districts/(create|<id>/edit|<id>/delete|<id>/toggle)`
  - POST `/admin/observers/(create|<id>/deactivate|<id>/password)`
- Observer
  - GET `/observer/dashboard`

### Auth & Permissions
- Teacher/Admin: Flask-Login user model + role checks for teacher routes
- Observer: separate session namespace stored in secure cookie; decorator `@observer_required`
- Student: session-only `student_id` for permissions; decorator `@student_required` where applicable (upload, react, comment)

### Forms & Validation (Flask-WTF)
- StartSessionForm: section, num_students, district, school, first_name, last_name, module; enforce uniqueness for active hour
- MediaForm: image_file, graph_tag, variable_tag (server-side type/size checks)
- ProjectForm: minimum 3 images; generate title
- CommentForm: text, optional parent_id
- Login forms: teacher/admin, observer, student PIN

### Media & Storage
- Dev: local filesystem under `uploads/`
- Prod: S3-compatible; centralize in `storage.py`; return absolute URLs for templates
- Pre/post save hooks: validate type/size, optional virus scanning, image resizing/thumbnailing

### Background Jobs
- `clear_expired_sessions` daily (not paused, >7 days old)
- Optional: image processing tasks (resize, thumbnail)

### Observability & Errors
- JSON logging with request ID, route, duration
- Error handlers for 400/401/403/404/500 (HTML and JSON)
- Sentry or similar (optional)

### Testing Strategy
- Unit tests for models and services
- Integration tests for routes (HTML + JSON)
- File upload tests with tmp storage
- Fixtures for users/sessions/students/media
- Coverage threshold gates in CI

### Deployment
- Gunicorn + Nginx (Linux) or platform equivalents; HTTPS
- Environment variables for DB, storage, broker, secrets
- Static via CDN, media via S3/CDN

### Non-Functional Requirements
- Security: CSRF, XSS mitigations, session cookie flags, password hashing
- Performance: pagination, indexing, storage offload
- Maintainability: clear blueprints, services, consistent error contracts


