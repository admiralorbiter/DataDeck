## Sequence Flows (High-Level)

Below flows outline request/response steps for critical user operations.

### 1) Teacher Creates a Session
1. Browser: GET `/start-session`
2. Server: Render form with teacher prefill
3. Browser JS: GET `/check-section-availability?section=H`
4. Server: Check active (non-archived) sessions for teacher+hour → JSON
5. Browser: POST form to `/start-session`
6. Server:
   - Ensure unique active hour
   - Create or update teacher district/school/first/last
   - Create `Session`
   - Generate N `Student`(name+PIN+avatar)
   - Redirect to `/session/<id>`

### 2) Student Login by PIN
1. Browser: POST `/student-login` with `student_password`
2. Server:
   - Lookup `Student` by PIN
   - Find their `Session`
   - Create or reuse account (Django) and log in; set `student_id` in session
   - Redirect `/session/<id>`

### 3) Upload Media (Image)
1. Browser: POST multipart `/upload/<session_id>` with `image_file`, `graph_tag`, `variable_tag`
2. Server:
   - Validate file and tags
   - Identify poster (student/admin)
   - Save file to storage
   - Create `Media` with generated title
   - Redirect `/session/<id>`

### 4) React with Badge
1. Browser: POST `/like-media/<media_id>/<badge_type>` (AJAX with CSRF)
2. Server:
   - Upsert `StudentMediaInteraction` for student+media
   - Update booleans per behavior (toggle or single-select)
   - Recalculate counts; persist on `Media`
   - Return JSON `{success, counts, user_like}`
3. Browser: Update UI counts and selected state

### 5) Comment on a Post
1. Browser: POST `/post/<media_id>` with `text` (and optional `parent_id`)
2. Server:
   - Create `Comment` with admin/student attribution
   - Increment `StudentMediaInteraction.comment_count` when student
   - Redirect back to `/post/<media_id>`

### 6) Observer Login and Dashboard
1. Browser: POST `/admin/login` (observer email+password)
2. Server:
   - Lookup `Observer` by email; verify password
   - Set `observer_id` in session
   - Redirect to `/observer/dashboard`
3. Dashboard Server-side:
   - Query teachers by `observer.district`
   - Collect sessions and recent media (limit 50)
   - Render dashboard


