## Future Opportunities & Enhancements

### UX & Engagement
- Real-time reactions/comments via WebSockets (Flask-SocketIO)
- Rich media support: video upload with server-side thumbnailing
- Image processing: automatic resizing, optimization, and thumbnails
- Improved gallery UX for projects (keyboard nav, zoom, captions)

### Moderation & Safety
- Moderation queue for media/comments with teacher approval
- Content scanning (antivirus + image content filters)
- Rate limiting for reactions/comments
- Audit logs for admin actions

### Auth & Identity
- SSO for teachers/observers (Google Workspace / Microsoft 365)
- Student identity abstraction (temporary PIN vs roster import)
- Passwordless observer invites with time-limited tokens

### Data & Analytics
- Teacher dashboard analytics (reaction distribution, participation over time)
- District-level analytics (engagement by school/teacher)
- Export datasets (CSV/Sheets) and API access (tokened)

### Platform & Ops
- S3-backed media with CDN; signed URLs for privacy
- Background jobs for media processing and scheduled tasks (Celery/RQ)
- Observability: structured logging, tracing, Sentry
- Feature flags for gradual rollouts

### Architecture & API
- API-first with OpenAPI spec; generate SDKs
- Versioned REST endpoints and pagination standards
- Consistent JSON error schema with error codes

### Curriculum & Content
- Built-in rubrics and rubric-based feedback instead of simple badges
- Templates for classroom modules and guided prompts
- Student portfolio pages across sessions

### Accessibility & Internationalization
- WCAG AA compliance; keyboard navigability
- i18n for UI strings; locale-based formatting


