## Data Migration Plan (Django → Flask)

### Goals
- Preserve core entities: Users (teachers), Observers, Districts, Sessions, Students, Media, Comments, StudentMediaInteractions
- Preserve file assets and URLs; normalize where needed
- Improve security where feasible (hash student PINs)

### Source vs Target
- Source DB: MySQL (prod) / SQLite (dev). Tables per Django models
- Target DB: SQLAlchemy schema matching `docs/FLASK_REWRITE_PLAN.md`
- Files: from local `/media` to local dev or S3/compatible in prod

### Strategy Options
1) One-time ETL and cutover (recommended)
   - Freeze Django app to read-only during migration window
   - Export tables to CSV/NDJSON; or query directly via SQLAlchemy connected to source
   - Transform rows to new schema; insert into Flask DB
   - Migrate files; rewrite paths/URLs
   - Smoke test; flip DNS
2) Dual-run with shared DB (not recommended)
   - Risky due to ORM differences and migrations; prefer clean ETL

### Field Mapping Highlights
- `CustomAdmin` → `User`
  - password: re-hash if algorithm differs; or force-reset teachers on first login in Flask
  - media_password: copy as-is (consider deprecating / encrypting)
- `Observer`
  - password: copy hash (pbkdf2_sha256) if supported; else force-reset
- `Session`
  - enforce uniqueness (created_by, section, is_archived=false) at application-level; add composite index
- `Student`
  - PIN: migrate as plaintext if present; in Flask, store hash and only display on export/generation
  - avatar_image_path: normalize to storage scheme (e.g., `static/...` → S3 URL or served static)
- `Media`
  - Files: copy to new storage; keep relative keys; update `project_images` to absolute URLs
  - Counts (graph/eye/read): keep cached counts; can recompute post-migration from interactions
  - **Note:** After migration, run `python manage.py rebuild_interactions` to ensure vote counts are accurate
- `Comment`, `StudentMediaInteraction`: direct copy; validate foreign keys exist

### File Migration
- Inventory all media paths (videos/images) and `project_images` entries
- For S3 target:
  - Upload with deterministic keys (e.g., `images/<media_id>_<uuid>.<ext>`) preserving existing where possible
  - Generate absolute URLs; update DB fields
- Validate referential integrity; produce a report of missing files

### Ordering & Dependencies
1) Districts → Users (teachers) → Observers → Sessions → Students → Media → Comments → Interactions
2) Files can be migrated while Media rows are created; finalize URLs update once upload completes

### Scripts (proposed)
- `scripts/export_from_django.py`: connect to Django DB, export to NDJSON
- `scripts/import_to_flask.py`: read NDJSON and insert via SQLAlchemy models
- `scripts/migrate_files.py`: copy/upload files and rewrite URLs
- `scripts/verify_integrity.py`: check counts (rows, FKs), sample media renders

### Verification Checklist
- Row counts per table within ±0.1%
- Random sampling (N=50) of sessions/media open successfully in Flask UI
- Reactions/comments interaction counts match recomputed totals
- Observer visibility limited to district scope
- Teacher dashboards show accurate students and sessions
- File hit ratio > 99.9%

### Rollback Plan
- Keep Django DB/files intact
- If verification fails, switch DNS back to Django and fix issues offline

### Post-Cutover Tasks
- Force password resets for teachers/observers if hashes changed
- Enable background jobs in production (clear-expired-sessions)
- Monitor logs for 48 hours; fix any migration edge cases


