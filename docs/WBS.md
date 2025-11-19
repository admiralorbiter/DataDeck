## Work Breakdown Structure (Flask Rewrite)

This WBS breaks the rewrite into epics → stories → granular subtasks with acceptance criteria (AC).

### Epic 1: Project Bootstrap & Tooling
- Story 1.1: App factory and config
  - Subtasks:
    - Create `create_app` with `Development/Testing/Production` configs
    - Load `.env` via python-dotenv
  - AC: `flask run` boots; toggling config flags changes behavior (DEBUG, DB URL)
- Story 1.2: Extensions wiring
  - Subtasks: SQLAlchemy, Alembic, Flask-Login, Flask-WTF, CSRF, Celery/RQ
  - AC: `alembic revision --autogenerate && alembic upgrade head` succeeds
- Story 1.3: Repo hygiene & CI
  - Subtasks: black/isort/flake8, pre-commit, pytest + coverage, Makefile
  - AC: `pytest` green; coverage ≥ 80%; pre-commit passes on clean repo

### Epic 2: Data Model & Migrations
- Story 2.1: Implement models
  - Subtasks: District, User, Observer, Session, Student, Media, Comment, StudentMediaInteraction
  - AC: Migrations apply; uniqueness/indexes enforced
- Story 2.2: Seed & fixtures
  - Subtasks: Dev seed CLI; pytest factories
  - AC: Seed creates teacher+district+session; factories generate valid entities

### Epic 3: Authentication & Roles
- Story 3.1: Teacher/Admin login/logout
  - Subtasks: routes, forms, templates, password hashing, role checks
  - AC: Valid login redirects to dashboard; invalid shows error
- Story 3.2: Observer login/logout (separate)
  - Subtasks: distinct blueprint, decorator `@observer_required`
  - AC: Observer-only routes blocked for non-observers
- Story 3.3: Student PIN session
  - Subtasks: PIN form; session store `student_id`; security notes
  - AC: Valid PIN redirects to session; invalid shows error; no Flask-Login user required

### Epic 4: Sessions Module
- Story 4.1: Start session (create)
  - Subtasks: WTForm, uniqueness (teacher+section active), module selection
  - AC: Duplicate active hour blocked; success redirects
- Story 4.2: Session page
  - Subtasks: pagination (12/page), filters (graph_tag, variable_tag), poster info annotations
  - AC: Filters persist in querystring; page render under 200ms (local)
- Story 4.3: Pause, archive/unarchive, delete
  - Subtasks: POST actions; flash messages; file cleanup on delete
  - AC: Archive restores original name; unarchive enforces uniqueness

### Epic 5: Student Management
- Story 5.1: Generate students
  - Subtasks: load CSV character sets; unique name/PIN; avatar pathing
  - AC: N unique students created; collisions avoided
- Story 5.2: Student list + delete
  - Subtasks: list per teacher; delete with ownership check
  - AC: Delete removes student and their interactions
- Story 5.3: Export cards PDF
  - Subtasks: PDF layout; multiple per page; download response
  - AC: PDF opens with correct info and layout

### Epic 6: Media Module
- Story 6.1: Upload image
  - Subtasks: form with `image_file`, `graph_tag`, `variable_tag` + validation; title generator
  - AC: Upload persists; title as "<poster>’s <graph_tag> <variable_tag>"
- Story 6.2: Edit media
  - Subtasks: update tags; recompute title consistently
  - AC: Save redirects to post; title updated
- Story 6.3: Delete media
  - Subtasks: permission checks; file removal via storage layer
  - AC: Media and files removed; 404 on revisit
- Story 6.4: Project upload (module 4)
  - Subtasks: minimum 3 images; main + additional; gallery data persisted
  - AC: Post page shows gallery with thumbnails & navigation

### Epic 7: Posts & Comments
- Story 7.1: Post detail
  - Subtasks: render media, poster, counts; reuse template partials
  - AC: Accurate counts and poster avatar
- Story 7.2: Comments + replies
  - Subtasks: nested tree; admin/student attribution; increment interaction `comment_count`
  - AC: Replies render nested; counts accurate

### Epic 8: Reactions/Badges
- Story 8.1: Decide reaction semantics
  - Subtasks: choose toggle or single-select; update UI and backend accordingly
  - AC: Unified behavior across session grid and post
- Story 8.2: API endpoint
  - Subtasks: POST `/media/<id>/react/<type>`; return `{success, counts, user_like}`
  - AC: UI updates counts and selection without reload

### Epic 9: Admin Dashboard
- Story 9.1: District CRUD + toggle
  - Subtasks: forms, checks to prevent delete when linked
  - AC: Create/edit/delete/toggle work with flash messages
- Story 9.2: Observer management
  - Subtasks: create, deactivate, change password
  - AC: Observer state updates appropriately
- Story 9.3: Teacher district assignment
  - Subtasks: change teacher’s district
  - AC: Reassignment reflected in observer views

### Epic 10: Observer Dashboard
- Story 10.1: District overview
  - Subtasks: list teachers; sessions; recent media (50)
  - AC: Observer sees only their district; no edits allowed

### Epic 11: Background Jobs
- Story 11.1: Clear expired sessions
  - Subtasks: schedule daily; delete not paused older than 7 days
  - AC: Job logs and deletes; unit test covers selection logic

### Epic 12: Storage & Static
- Story 12.1: Storage abstraction
  - Subtasks: local dev; S3 prod; URL builder
  - AC: Files saved/retrieved via unified API; templates use absolute URLs

### Epic 13: Observability & Errors
- Story 13.1: Logging
  - Subtasks: JSON logs; request IDs; error logging
  - AC: Logs include route, latency, status, correlation ID
- Story 13.2: Error handlers
  - Subtasks: 400/401/403/404/500 HTML + JSON
  - AC: Friendly pages; consistent JSON structure

### Epic 14: Testing
- Story 14.1: Model tests
  - Subtasks: constraints, methods, relationships
  - AC: 100% coverage for models
- Story 14.2: Route tests
  - Subtasks: auth, sessions, media, posts, reactions, admin, observer
  - AC: 80% global coverage

### Epic 15: Migration & Cutover
- Story 15.1: ETL scripts
  - Subtasks: export from Django DB; import into Flask DB; file migration
  - AC: Sample migration succeeds in staging
- Story 15.2: Parallel run + validation
  - Subtasks: verify routes & data parity; stakeholder sign-off
  - AC: Go/no-go decision checklist completed


