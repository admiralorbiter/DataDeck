## DataDeck Architecture (Current Django Implementation)

### Purpose
DataDeck enables teachers to run classroom “sessions” where students upload data visualizations (images), react with badges (Graph/Eye/Read), and add comments. District-level observers can browse activity across teachers in their district.

### Roles
- **Teacher/Admin (`CustomAdmin`)**: Creates sessions, generates students, uploads/moderates media, manages districts and observers.
- **Student**: Logs in with PIN, uploads media or final projects, reacts with badges, comments.
- **Observer**: Logs in with email/password, views sessions and media for their district.

### Tech Stack (current)
- Django 5 (server-rendered HTML via templates)
- Database: MySQL (prod) / SQLite (dev/tests)
- Celery configured (scheduled clear-expired-sessions task); currently not required to run per README
- Static via Whitenoise; media stored on local filesystem
- Pytest for tests

### Key Features
- Session lifecycle: create, list, pause, archive/unarchive, delete
- Student generation: unique character name + PIN, avatar assignment from CSVs and images
- Media uploads: image upload (module 2), multi-image project gallery (module 4)
- Reactions/badges: Graph guru, Expert engager, Supreme storyteller
- Comments: nested replies, admin/student attribution
- Observer dashboard: view activity for district
- District/admin management: CRUD for districts and observers
- Student export: PDF cards with names and PINs

### Data Model
Mermaid ER diagram of the current Django entities and relationships:

```mermaid
erDiagram
  "District" {
    BIGINT id PK
    VARCHAR name "unique"
    VARCHAR code "unique"
    BOOLEAN is_active
    DATETIME created_at
  }
  "CustomAdmin" {
    BIGINT id PK
    VARCHAR username
    VARCHAR password_hash
    VARCHAR school
    BIGINT district_id FK
    VARCHAR first_name
    VARCHAR last_name
    VARCHAR media_password "nullable"
    VARCHAR profile_picture "nullable"
  }
  "Observer" {
    BIGINT id PK
    VARCHAR name
    VARCHAR email "unique"
    VARCHAR password_hash
    BIGINT district_id FK
    BOOLEAN is_active
    BIGINT created_by_id FK
    DATETIME created_at
  }
  "Session" {
    BIGINT id PK
    VARCHAR name
    VARCHAR original_name "nullable"
    CHAR session_code "8, unique"
    INT section
    ENUM module "{'2','4'}"
    DATETIME created_at
    BOOLEAN is_paused
    BOOLEAN is_archived
    DATETIME archived_at "nullable"
    BIGINT created_by_id FK
    VARCHAR character_set
  }
  "Student" {
    BIGINT id PK
    VARCHAR name
    VARCHAR pin "stored as plaintext"
    BIGINT section_id FK
    BIGINT admin_id FK
    VARCHAR device_id "nullable"
    TEXT character_description
    VARCHAR avatar_image_path
  }
  "Media" {
    BIGINT id PK
    BIGINT session_id FK
    VARCHAR title
    TEXT description "nullable"
    ENUM media_type "{'video','image','comment'}"
    VARCHAR video_file "nullable"
    VARCHAR image_file "nullable"
    DATETIME uploaded_at
    INT graph_likes
    INT eye_likes
    INT read_likes
    ENUM graph_tag "subset"
    BOOLEAN is_graph
    ENUM variable_tag "subset"
    VARCHAR submitted_password "nullable"
    BIGINT student_id FK "nullable"
    BIGINT posted_by_admin_id FK "nullable"
    UUID project_group "nullable"
    JSON project_images "nullable"
    BOOLEAN is_project
  }
  "StudentMediaInteraction" {
    BIGINT id PK
    BIGINT student_id FK
    BIGINT media_id FK
    BOOLEAN liked_graph
    BOOLEAN liked_eye
    BOOLEAN liked_read
    INT comment_count
    DATETIME created_at
    DATETIME updated_at
  }
  "Comment" {
    BIGINT id PK
    BIGINT media_id FK
    BIGINT parent_id FK "nullable, self"
    TEXT text
    DATETIME created_at
    DATETIME updated_at
    VARCHAR name
    VARCHAR device_id "nullable"
    BOOLEAN is_admin
    BIGINT student_id FK "nullable"
    VARCHAR admin_avatar "nullable"
  }

  "District" ||--o{ "CustomAdmin" : "district"
  "District" ||--o{ "Observer" : "district"
  "CustomAdmin" ||--o{ "Session" : "created_by"
  "Session" ||--o{ "Student" : "section"
  "CustomAdmin" ||--o{ "Student" : "admin"
  "Session" ||--o{ "Media" : "session"
  "CustomAdmin" ||--o{ "Media" : "posted_by_admin"
  "Student" ||--o{ "Media" : "student"
  "Media" ||--o{ "Comment" : "comments"
  "Comment" ||--o| "Comment" : "replies"
  "Student" ||--o{ "StudentMediaInteraction" : "student"
  "Media" ||--o{ "StudentMediaInteraction" : "media"
  "Student" ||--o{ "Comment" : "student"
```

### Route Inventory (current)
Key Django routes defined in `video_app/urls.py` and `datadeck/urls.py`:
- Auth: `/student-login/`, `/student-logout/`, `/admin/login/`
- Home: `/`
- Teacher: `/teacher_view/`, `/update_teacher_info/`, `/set-media-password/`
- Sessions: `/start-session/`, `/session/<id>/`, `/session/<id>/(delete|pause|archive)`, `/check-section-availability/`
- Students: `/student/<id>/`, `/delete-student/<id>/`, `/download-students/`, `generate_new_students`
- Media: `/upload/<session_id>/`, `/upload-project/<session_id>/`, `/edit-media/<id>/`, `/delete-media/<id>/`, `/like-media/<id>/<type>/`
- Posts: `/post/<media_id>/`
- Observer: `/observer/dashboard/`, `/observer/logout/`
- Admin Dashboard: `/admin-dashboard/` + District and Observer management helpers

### Core Flows (high-level)
- Teacher creates session → validate unique active hour → generate students → redirect to session
- Student logs in with PIN or join via `session_code` → sets `student_id` in session → redirect to session
- Upload media → validate form → attach poster (student/admin) → save file → create `Media`
- React (badge) → upsert `StudentMediaInteraction` → recalc media counts → return JSON
- Comment → create `Comment` (+ optional parent) → increment interaction `comment_count`
- Observer login → session flags `observer_id` → district dashboard view

### Security Model
- CSRF enabled for forms and AJAX
- Student PINs stored plaintext; Django user created with PIN as password on first login (improve in rewrite)
- Observer authentication via email+hashed password; restricted via middleware and decorators
- Access checks in views for deleting/editing media and comments

### Background Jobs
- `video_app.tasks.clear_expired_sessions`: delete sessions older than 7 days when not paused (scheduled daily)

### Static & Media
- Static assets in `video_app/static/`
- Media files stored under `/media` (local fs). Project images stored as URL strings in `Media.project_images` JSON

### Known Gaps / Risks
- Mixed reaction semantics (toggle vs single-select) across endpoints
- Student PINs not hashed; creates Django users dynamically
- Media storage local-only; lack of virus scanning and image resizing
- Observer/Teacher logins share `/admin/login/` path; UX and boundary can be clearer
- Error handling in file deletion is best-effort; no centralized storage abstraction


