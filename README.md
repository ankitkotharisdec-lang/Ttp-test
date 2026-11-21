# Step2Success — Django stage 1

Runnable Django app with SQLite, a database-driven roadmap, content administration,
JSON read endpoints and fixed-template lesson pages. No React required: the pasted
Gemini code is plain HTML/CSS, not React, and was truncated after `.page-title`.
The included page is a functional matching-style replacement, not a complete reproduction
of the missing source.

## Run locally (Python 3.12; macOS/Linux)

```bash
cd step2success_backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_python
python manage.py createsuperuser
python manage.py runserver
```

Windows: activate with `.venv\Scripts\activate` and use `python` instead of `python3`.

Open http://127.0.0.1:8000/ for the roadmap and http://127.0.0.1:8000/admin/
for content administration. No credentials are pre-created. The bundled SQLite
file contains sample content only; it is also safe to start without it and run the
migration/seed commands above. Seeding is for initial setup and matches titles;
if you rename sample items and reseed, old sample titles can be recreated.

## Content workflow

1. Create a course (slug `python`) and mark it published.
2. Add sections (tabs) under the course; mark them published.
3. Open a section and add chapters, assigning positions.
4. Open a chapter and add lesson titles; save, then open a lesson to edit its body.
5. Fill explanation, code, output, optional video URL and summary.
6. Mark content published. Refresh the student page to fetch changes.

Every ancestor must be published. Counts include published lessons only.
Positions need not be consecutive; IDs break ties. Set distinct positions for
intentional ordering. Deletions of parents with children are blocked.

No live polling: updates appear on reload. Chapter content is public in this
stage. Payments, student accounts/progress, trials, quizzes, private content,
rich text editing, Wagtail, uploads and draft revision history are not implemented.
The video field opens a link, not an embedded player. Text is HTML-escaped.

## API

- GET `/api/courses/python/outline/`: course and nested published sections/chapters;
  each chapter includes id, title, position, lesson_count.
- GET `/api/chapters/<uuid>/lessons/`: published lesson metadata.
- GET `/lessons/<uuid>/`: rendered lesson page.

Only GET is accepted by these views. All writes are through Django admin with
Django permissions and CSRF. Outline loads in three database queries.
See `learning/static/learning/app.js` for fetch, tab filtering, roadmap layout,
loading/error/empty states, and lesson popup wiring.

## Connect the full Gemini page later

Move the complete HTML to `learning/templates/learning/roadmap.html`. Move CSS/JS
into `learning/static/learning/`. Load assets with Django's `{% static %}` tag.
Fetch `/api/courses/python/outline/`, select the first section and pass its
`chapters` array to your existing renderer. Use chapter UUIDs for clicks; don't
identify records by display numbers. Never expose database credentials to JavaScript.
Keep the admin Add Chapter controls separate from the public student page.

## Optional Supabase PostgreSQL

SQLite works immediately. A Supabase account/credentials have NOT been connected
or tested. Use a fresh project/database or review existing tables before migrating.
This app uses Django-managed `learning_*` tables, not the earlier manually created
`courses`/`chapters` tables. It uses Django auth, not Supabase Auth.

Set DATABASE_URL in your shell using the PostgreSQL connection URI from your
Supabase project's Connect panel. Use a suitable direct or session-pooler endpoint
for migrations and append `sslmode=require` as appropriate to that URI. URI-encode
special characters in passwords. Keep it secret; do not put it into HTML or git.

```bash
export DATABASE_URL='postgresql://USER:PASSWORD@HOST:PORT/postgres?sslmode=require'
python manage.py migrate
python manage.py seed_python
python manage.py createsuperuser
```

Setting DATABASE_URL switches databases; it does NOT transfer SQLite records.
For real data migration, export/import the learning records with Django dumpdata/
loaddata after migrating PostgreSQL, taking backups first. Staff accounts must be
created or migrated separately. Do not expose these Django-managed tables through
Supabase's public Data API; keep browser access routed through Django.

## Validation

```bash
python manage.py check
python manage.py test
```

Tests cover published counts, hidden ancestors, admin-only writes, ordering,
query count, text escaping, roadmap response and repeatable seeding.

## Deployment boundary

This is a local stage-1 starter, not a production deployment. SQLite is not suitable
for Cloud Run's ephemeral filesystem or multiple application instances. Before
Cloud Run use PostgreSQL, a production WSGI server, static-file serving/CDN,
DJANGO_DEBUG=0, a secret DJANGO_SECRET_KEY, DJANGO_ALLOWED_HOSTS, HTTPS/proxy
configuration and backups. DEBUG defaults on ONLY to make local setup easy.
Dependencies are pinned to the versions installed during this build; update them
through normal security maintenance.

## Supabase (database + login)

- **Database:** set `DATABASE_URL` to your Supabase Postgres URI (see `.env.example`), then run `python manage.py migrate --fake-initial` (the Course/Section/Chapter/Lesson tables already exist in Supabase, so the first learning migration is marked as applied; the Python course then seeds itself). Without `DATABASE_URL` the app still uses local SQLite.
- **Login:** Supabase Auth handles sign-up/log-in (`/signup/`, `/login/`, `/account/`). Set `SUPABASE_URL` and `SUPABASE_PUBLISHABLE_KEY`.
- **Users and plans:** each new Supabase user automatically gets a `public.profiles` row (`plan` = `free` or `paid`, `plan_status`, `plan_started_at`, `plan_expires_at`) and a `public.subscriptions` history row. Users can read their own rows and edit only name and phone; plan changes must come from the server.
- After `migrate`, Django enables row level security on its own tables so they are not readable through Supabase's public REST API.
