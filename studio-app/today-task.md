You are working on an existing AI image generation prototype called Avision Studio.

Goal:
Convert this prototype into a production-ready AI SaaS application while preserving the existing AI generation functionality.

Do not rewrite the entire project. First inspect the existing architecture, understand the current frontend, backend, API flow, and AI generation workflow. Then propose changes and implement incrementally.

The target architecture should evolve through these stages:

==================================================
STAGE 1 — PRODUCTION FOUNDATION
==================================================

Convert the prototype backend into a scalable SaaS foundation.

Implement:

1. Backend Architecture
- Refactor FastAPI into a modular production structure.
- Separate:
  - API routes
  - services
  - database models
  - schemas
  - business logic
  - configuration
  - background tasks

2. Database
Add PostgreSQL integration.

Create database models for:

Users:
- id
- email
- password hash
- role
- created_at
- updated_at

Projects:
- id
- user_id
- name
- created_at

AI Jobs:
- id
- user_id
- project_id
- status
- prompt
- created_at
- completed_at
- error_message

Generated Images:
- id
- user_id
- project_id
- job_id
- prompt
- image_url or file_path
- created_at

Notifications:
- id
- user_id
- type
- message
- read_status
- created_at

Audit Logs:
- id
- user_id
- action
- timestamp


3. Authentication
Implement:

- User registration
- Login
- JWT authentication
- Password hashing
- Protected API routes
- User/admin roles


4. Redis and Background Jobs

Move AI generation from direct request-response into asynchronous jobs.

Current:

User request
→ AI API
→ Return result


Target:

User request
→ Create AI Job
→ Store job in database
→ Add task to Redis queue
→ Worker processes AI generation
→ Save result
→ Update job status


Support statuses:

- pending
- processing
- completed
- failed


5. Configuration

Implement:

- Environment variables
- Separate development and production settings
- Proper logging
- Error handling


==================================================
STAGE 2 — AI SaaS FEATURES
==================================================

Transform the application into a real AI SaaS product.

Implement:

1. User Workspace

Users should have:

- Workspace
- Projects
- Generation history
- Saved results


2. AI Credit System

Implement SaaS quota logic.

Create:

Plans:

- Free
- Pro
- Enterprise


Each plan has:

- monthly credits
- generation limits


Example:

Free:
100 credits


Every AI generation:

User credits
→ check balance
→ consume credits
→ create AI job


3. Subscription Model

Do not integrate real payment yet.

Create subscription architecture:

Subscription table:

- user_id
- plan
- status
- start_date
- expiry_date


Implement:

- Free subscription by default
- Admin ability to upgrade user plan
- Simulated subscription activation


Prepare architecture so real payment webhooks can be added later.


4. Image Storage

For now:

Use simple storage suitable for MVP.

Do not implement AWS S3 yet.

Create a storage abstraction layer:

StorageService:

- save()
- delete()
- get_url()


Initial implementation:

- local VPS disk storage

Future replacement:

- S3
- Cloudflare R2
- other object storage


Do not store image binary data inside PostgreSQL.

Store only metadata and file location.


5. User Dashboard

Create frontend pages:

User:

- Dashboard
- Projects
- Generation History
- Credits
- Profile


Admin:

- Users
- AI Jobs
- Usage


==================================================
STAGE 3 — BUSINESS OPERATIONS AUTOMATION
==================================================

Add operational workflows similar to a real SaaS company.

Implement:

1. Email System

Add transactional email integration.

Use an email API provider.

Create:

- Email verification
- Password reset
- Generation completed notification
- Low credit warning


Do not create a mail server.

Use external email API.


2. Notification System

Create internal notification center.

Examples:

- AI generation completed
- AI generation failed
- Credits running low
- Subscription changed


3. Workflow Logging

Create business workflow logs.

Example:

User Registration:

User registered
→ Account created
→ Free credits allocated
→ Welcome email sent


AI Generation:

Request created
→ Job queued
→ Worker started
→ AI completed
→ Result saved
→ Notification sent


4. Admin Business Intelligence Dashboard

Create dashboard showing:

Users:

- total users
- active users
- new registrations


AI Usage:

- total generations
- successful jobs
- failed jobs
- average generation time


Business:

- free users
- pro users
- credit consumption


System:

- queue status
- errors
- API failures


5. Audit System

Track important actions:

- Login
- Registration
- Credit usage
- Plan changes
- Admin actions


==================================================
IMPORTANT ENGINEERING RULES
==================================================

- Do not break existing AI generation functionality.
- Preserve current frontend functionality.
- Implement incrementally.
- Before changing architecture, explain the current code structure.
- Prefer clean modular design over quick hacks.
- Avoid unnecessary complexity.
- Build reusable services.
- Make future integration with external automation tools possible through APIs and webhooks.
