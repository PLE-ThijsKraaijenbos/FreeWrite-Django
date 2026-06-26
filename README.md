# FreeWrite (Backend / API)

The Django + DRF backend for FreeWrite, a mobile self-help app built around
narrative therapy. It serves the [React Native app](../FreeWrite-React-Native).

## What's in here

The API lives under `api/` and is split into three Django apps, one per domain:

| App | What it covers |
| --- | --- |
| **user** | Register, login, JWT refresh, profile/onboarding, coins, and the avatar editor (unlock and equip items). |
| **journey** | The user's path of writing exercises, grouped into phases. Steps unlock one after another, and the endpoints read the journey and move a step through its lifecycle (start, complete, bookmark). |
| **community** | The shared feed where users post, browse, tag, and like each other's writing. Posts can have an optional image. |

Each app has the same layout: `models.py`, `serializers.py`, `services.py`,
`views.py`, `urls.py`, `exceptions.py`, `admin.py`.

## Architecture

A few choices worth knowing before you read the code:

- **Per-domain apps.** `user`, `journey` and `community` are separate Django
  apps so each domain's models, logic and routes stay together.
- **Service layer.** Business logic lives in `*Service` classes in `services.py`
  (e.g. `JourneyService`, `PostService`), not in the views or models. Views stay
  thin (parse the request, call a service, return a response), and the logic is
  reusable and testable without going through HTTP.
- **Views: generics for CRUD, APIView for actions.** Plain list/detail endpoints
  use DRF's generic views (`ListAPIView`, `ListCreateAPIView`). The action
  endpoints (start a step, complete, bookmark, like/unlike) use a plain
  `APIView` instead, because they aren't CRUD on a resource, they're one-off
  state changes. Mapping those onto a ViewSet + router is more trouble than it's
  worth, so each gets an explicit URL and a single method.
- **Custom exceptions.** Domain errors are `APIException` subclasses in
  `exceptions.py` (e.g. `StepNotAvailable`, `StepAlreadyCompleted`) that already
  carry their HTTP status, so services can just raise them.
- **Safe state transitions.** Journey actions run inside a transaction with
  `select_for_update`, so two requests can't complete the same step or hand out
  coins twice.
- **Data-driven unlocking.** Which steps a user gets is decided by an
  `activation_rules` JSON field on each step, matched against the user's profile,
  instead of being hardcoded.
- **JWT auth.** Stateless auth via SimpleJWT. `IsAuthenticated` is the default
  permission.
- **Schema-first docs.** drf-spectacular generates the OpenAPI schema and Swagger
  UI from the views.

## Data model

- **Journey > Phase > JourneyStep.** A phase has an ordered list of steps. The
  phase names (Externalisation, Deconstruction, etc.) aren't hardcoded, you
  author them as content in the admin.
- **One step, one minigame.** A `JourneyStep` has an `assignment_type` plus a
  nullable one-to-one link to each of the six minigame content tables
  (`journal`, `letter`, `choice_story`, `speech_bubble`, `bubble_pop`, `scale`).
  Only the link matching the type is filled in. Each minigame keeps its own real
  table and fields, and the journey query prefetches them all in one go.
- **JourneyStepProgress** is the per-user, per-step state: status
  (`UNAVAILABLE`, `AVAILABLE`, `IN_PROGRESS`, `COMPLETED`), bookmark, timestamps,
  and the user's saved responses.
- **User** has a profile with coins, and **AvatarItem** / **UserAvatarItem**
  handle the avatar editor (price, what's owned, what's equipped).

There's no seed script or fixtures. Migrations are schema only, so all the
content (phases, steps, minigame content, avatar items) is created through the
admin at `/admin/`.

## Tech stack

- Django + Django REST Framework
- PostgreSQL (via `dj-database-url`)
- SimpleJWT for auth, drf-spectacular for the schema and docs
- django-unfold for the admin theme
- Cloudinary for post images, WhiteNoise for static files
- Docker for local dev, Railway for hosting

## Getting it running (Docker)

Everything runs in Docker: Postgres, Django, and an ngrok tunnel.

1. Copy the env template and fill it in:

   ```bash
   cp .env.example .env
   ```

2. Start it up:

   ```bash
   docker compose up
   ```

   That runs migrations, collects static files, and serves the API on
   **http://localhost:8000**.

3. In another terminal, make an admin user so you can add content:

   ```bash
   docker compose exec django python manage.py createsuperuser
   ```

### Handy URLs

| URL | What it is |
| --- | --- |
| `/api/docs/` | Swagger UI (interactive API docs) |
| `/api/schema/` | Raw OpenAPI schema |
| `/admin/` | Admin panel for authoring content |
| `/api/health/` | Health check |

## The endpoints

Base path is `/api/`. Auth is JWT, so you send `Authorization: Bearer <access>`.
Access tokens last 5 minutes, refresh tokens last 7 days. Register, login, token
refresh and health need no token.

| Method and path | What it does |
| --- | --- |
| `POST /user/register/` | Create an account (returns tokens). |
| `POST /user/login/` | Log in (returns tokens). |
| `POST /user/token/refresh/` | Trade a refresh token for a fresh access token. |
| `POST /user/complete-profile/` | Finish onboarding / profile. |
| `GET  /user/profile/` | The current user's profile, including coins. |
| `GET  /user/avatar/items/` | List the avatar editor items. |
| `POST /user/avatar/items/{id}/unlock/` | Unlock an item with coins. |
| `POST /user/avatar/items/{id}/equip/` | Equip an item you own. |
| `GET  /journey/` | The user's journey (phases, steps, progress). |
| `POST /journey/progress/{id}/start/` | Start a step. |
| `POST /journey/progress/{id}/complete/` | Complete a step. |
| `POST /journey/progress/{id}/bookmark/` | Toggle a bookmark. |
| `GET  /community/tags/` | List tags. |
| `GET/POST /community/posts/` | List or create posts (create takes `multipart/form-data` for an image). |
| `GET/.../community/posts/{id}/` | Get, update or delete a post. |
| `POST /community/posts/{id}/like/` | Like or unlike a post. |

The Swagger UI at `/api/docs/` is the real source of truth, this table is just a
summary.

## About ngrok
The `ngrok` service in `docker-compose.yml` puts the local API behind a public
HTTPS URL. It's there for mobile development: a real phone running the Expo dev
client needs to reach the backend, and ngrok saves you from messing with
`expo tunnel` or firewall rules.

You can change the URL from `.env`:

```env
NGROK_AUTHTOKEN=your-ngrok-authtoken
NGROK_DOMAIN=your-subdomain.ngrok-free.app
```

Point the app's `EXPO_PUBLIC_FREEWRITE_API_URL` at the same domain. Whatever
`NGROK_DOMAIN` you use also needs to be in `ALLOWED_HOSTS`,
`CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS`.

## Environment variables

| Variable | What it's for |
| --- | --- |
| `SECRET_KEY` | Django secret key (use a long random string). |
| `DEBUG` | `True` locally, `False` in production. |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts. |
| `CORS_ALLOWED_ORIGINS` | Comma-separated origins allowed to call the API. |
| `CSRF_TRUSTED_ORIGINS` | Comma-separated trusted origins for CSRF. |
| `DATABASE_URL` | Postgres connection string. |
| `NGROK_AUTHTOKEN` | ngrok auth token for the dev tunnel. |
| `NGROK_DOMAIN` | ngrok subdomain to expose the API on. |
| `CLOUDINARY_CLOUD_NAME` | Cloudinary cloud name (post images). |
| `CLOUDINARY_API_KEY` | Cloudinary API key. |
| `CLOUDINARY_API_SECRET` | Cloudinary API secret. |

## Deployment

Hosted on Railway (see `railway.toml`). On deploy it runs migrations, collects
static files, and serves through Gunicorn bound to `$PORT`.
