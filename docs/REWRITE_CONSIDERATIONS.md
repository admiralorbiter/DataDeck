## Fresh Rewrite Considerations (Tooling, Data, Features, Architecture, UX)

This document enumerates decisions and options to consider before/during a clean rewrite on Flask. It spans product, UX, architecture, security, data, operations, testing, and developer experience. Pick and choose; use as a checklist.

### Product & UX
- Personas & goals
  - Teacher/Admin: create sessions, manage students, review submissions, moderate
  - Student: easy login (PIN), upload/submit, react, comment, view peers
  - Observer: district-wide read-only visibility and insights
- Information architecture
  - Clarify terminology: Session vs Class vs Hour; Module types
  - Navigation for roles; quick switching among hours; breadcrumbs
- Onboarding & demos
  - Demo mode with sample data; guided tours; tooltips
  - First-run checklist (set district/school, create hour, generate students)
- Upload UX
  - Drag-and-drop, paste-from-clipboard
  - Client-side validation (type/size/dimensions), progress bars, resumable uploads (tus/Multipart)
  - Image preview & basic editing (crop/rotate)
- Reactions & comments
  - Decide semantics: single-select vs multi-toggle; visual clarity
  - Inline comments on images (annotations) vs thread below
  - Mentions (@student), emoji reactions (optional)
- Discoverability & feedback
  - Filters (tags, poster, time), search
  - Sorting (most recent, most reacted, most commented)
  - Badges tooltips and rubric links
- Accessibility (A11y)
  - Keyboard navigation, ARIA roles, focus states
  - Color contrast; alternative text requirements for images
  - Screen reader-friendly structure
- Internationalization (i18n/l10n)
  - Translatable strings; date/number formats; RTL readiness if needed
- Mobile responsiveness
  - Touch targets; responsive grids; performance on low-end devices
- Performance UX
  - Skeleton loading, lazy loading images, pagination/infinite scroll
  - Optimistic UI for reactions; toasts
- Classroom safety & moderation
  - Teacher approval queue for media/comments
  - Soft-delete with undo; audit trails
  - Word filters/flagging; rate limiting

### Domain & Data Modeling
- Students
  - PIN strategy: one-way hash storage; printable cards; rate-limited login
  - Roster import (CSV/Google Classroom) vs generated characters
  - Persistent identifiers vs per-session ephemeral students
- Sessions
  - Uniqueness rule (teacher, hour, active) enforced at DB + app
  - Archival policies; retention periods and auto-archive
- Media
  - Store original + derivatives (thumbnails); EXIF handling
  - Metadata: dimensions, size, mime, checksum (ETag)
  - Project gallery: distinct table for images vs JSON array
- Reactions
  - Canonical implementation (toggle vs radio) and DB constraints
  - Anti-spam limits; per-student uniqueness
- Comments
  - Depth, ordering, editing window, soft delete
  - Abuse reporting and teacher moderation
- Districts & multi-tenancy
  - Tenant isolation by district; per-tenant settings; subdomains

### Architecture & Patterns
- Monolith first with clear modular boundaries (Blueprints + service layer)
- Domain services for core operations (student generation, upload, reactions)
- API-first design with OpenAPI; consistent JSON errors
- DTO/schema validation (Pydantic/Marshmallow)
- Templated SSR first; consider htmx or sprinkle React where useful
- Background workers (Celery/RQ) for long-running tasks
- Feature flags for incremental rollout (Flask-FeatureFlags/Unleash)
- ADRs (Architecture Decision Records) to capture major choices

### Tooling & Libraries
- Core
  - Flask, SQLAlchemy, Alembic, Flask-Login, Flask-WTF (CSRF)
  - Pydantic/Marshmallow for request/response validation
  - Celery or RQ (+ Redis) for jobs; APScheduler for simple schedules
- Frontend
  - Bootstrap 5 or Tailwind; icons (Font Awesome or Heroicons)
  - htmx/Alpine.js for progressive enhancement, or React if SPA needed later
- Quality
  - black, isort, flake8, mypy (optional), pre-commit
  - pytest, coverage; hypothesis for property tests (optional)
- Observability
  - structlog/loguru; Sentry; Prometheus + Grafana (via exporters)
- Security
  - passlib for hashing; Flask-Talisman (CSP, security headers)
  - Safety/pip-audit/dependabot for dependency scanning

### Storage & Files
- Use S3-compatible storage in prod; local for dev/tests
- Presigned uploads from browser; server verifies and records metadata
- On-upload processing: virus scan (ClamAV/Lambda), EXIF strip, resize/thumbnail
- Content delivery via CDN; cache headers and invalidation strategy

### Database & Performance
- Index strategy: cover frequent filters (session_id, tags, uploaded_at)
- Query hygiene: eager loading to avoid N+1; measure with query profiler
- Pagination standards (cursor or page+size); limits and defaults
- Connection pooling; retries; timeouts
- Caching layer (Redis) for hot lists (leaderboard, counts) if needed

### Security & Compliance
- Authentication
  - Teachers/Observers: email+password; optional SSO (Google/Microsoft)
  - MFA for admins (TOTP/WebAuthn)
  - Session management: secure cookies, rotation on privilege changes
- Authorization
  - RBAC: roles (teacher, district_admin, observer, student), resource scoping
  - Row-level checks for district/teacher ownership
- Web security
  - CSRF across forms/AJAX; CORS policy if exposing APIs
  - CSP, HSTS, referrer policy; input validation/sanitization (comments)
- Abuse prevention
  - Rate limiting (login, reactions, comments); IP throttling; CAPTCHA fallback
- Privacy & compliance
  - COPPA/FERPA considerations; DPA templates; data retention policies
  - PII minimization; encryption at rest (DB, object store) and in transit (TLS)

### Background Jobs & Scheduling
- Clear expired sessions daily; configurable retention
- Media processing pipeline (resize, optimize, virus scan)
- Periodic exports or backups (DB + media)
- Monitor queues and failures; retry/backoff strategies

### Observability & Operations
- Structured logs with request IDs; correlation across worker and web
- Metrics: request latency, error rates, queue depth, job failures
- Tracing (OpenTelemetry) for complex flows (uploads, processing)
- Alerts: SLOs (99th percentile latency), error budget, on-call runbooks

### Testing & QA
- Unit tests: models/services
- Integration tests: routes (HTML + JSON); file uploads using tmp dirs
- E2E smoke tests for key flows (create session, student login, upload, react, comment)
- Load testing (k6/Locust) for class-size scenarios
- Accessibility audits (axe) and Lighthouse performance checks

### Dev Experience
- Makefile/Invoke tasks (`make run`, `make test`, `make lint`, `make seed`)
- Docker for dev parity (Compose with DB, Redis, S3 emulator like MinIO)
- Pre-commit hooks; PR templates; CODEOWNERS
- Conventional commits; semantic versioning; CHANGELOG
- ADRs and living docs in `docs/`

### Deployment & Infrastructure
- Containers (Docker) and CI/CD (GitHub Actions)
- Environments: dev/staging/prod with separate creds
- Rollouts: blue/green or canary; database migrations with zero-downtime plan
- Health checks, readiness/liveness probes; backups and restores
- Cost awareness: lifecycle policies for media; logs retention

### API & Integrations
- OpenAPI spec; Swagger UI for dev
- API keys or OAuth for third-party integrations (future)
- Webhooks for events (submitted, reacted, commented)

### Analytics & Insights
- Event tracking (privacy-conscious): uploads, reactions, comments, retention
- Teacher/district dashboards; export CSV/Sheets
- Data warehouse pipeline (optional): CDC or nightly dumps

### Content & Curriculum Support
- Built-in rubrics and grading workflows
- Module templates with prompts and examples
- Student portfolio pages across sessions

### Roadmap & Governance
- MVP scope: parity with current core features (sessions, students, uploads, reactions, comments)
- Phase 2: observer analytics, moderation, S3/CDN, real-time updates
- Phase 3: SSO, rubrics, webhooks/API, advanced analytics
- Governance: design reviews, security reviews, release checklist

### Edge Cases & Small Details
- Large image handling; graceful failure and retries
- Duplicate uploads detection (hashing)
- Timezone handling (server vs user locale)
- Browser support policy (Chromium/Firefox/Safari; iPadOS in classrooms)
- Offline-safe interactions (queue reactions for retry)
- Friendly 404/500 pages; consistent empty states


