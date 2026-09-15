# Shashwamie's Portfolio

A portfolio site built with [Django](https://docs.djangoproject.com/en/6.1/) +
[Wagtail](https://docs.wagtail.org/en/stable/) for content management, styled
with [Tailwind CSS](https://tailwindcss.com/) using a design-token system
inspired by [shadcn/ui](https://ui.shadcn.com/docs) (dark, cyberpunk-leaning,
magenta/purple accent).

## Stack

- Python (managed via [uv](https://docs.astral.sh/uv/)), Django 6, Wagtail 8
- Tailwind CSS v4 via `django-tailwind` (Node/npm builds the CSS; no other
  JS framework — pages are server-rendered Django/Wagtail templates)
- SQLite for local dev; ready to switch to Postgres in production via
  `DATABASE_URL`

## First-time setup

```bash
# Python deps + venv
uv sync

# Tailwind's Node deps
uv run python manage.py tailwind install

# Database + your own admin login
uv run python manage.py migrate
uv run python manage.py createsuperuser

# Optional: copy and fill in .env for a real SECRET_KEY locally
cp .env.example .env
```

## Running locally

Runs the Django dev server and the Tailwind CSS watcher together:

```bash
uv run python manage.py tailwind dev
```


Then visit:

- `http://localhost:8000/` — the site
- `http://localhost:8000/cms/` — the Wagtail admin (content editing)
- `http://localhost:8000/django-admin/` — Django's own admin (users/groups)

(Or run `uv run python manage.py runserver` and
`uv run python manage.py tailwind start` in two separate terminals if you'd
rather not use the combined `dev` command. `tailwind dev` runs both via
[honcho](https://pypi.org/project/honcho/) and `Procfile.tailwind`.)

## Adding a project

Everything under **Projects** is managed from the Wagtail admin — no code
changes needed:

1. Go to `/cms/`, open **Pages → Home → Projects**, and add a child
   **Project Page**.
2. Fill in the summary, cover image, tech stack tags, links, dates, and the
   body (paragraphs / images / code snippets).
3. Check **Featured** to have it show up in the "Featured projects" section
   on the homepage.
4. Publish.

## Project structure

```
config/            Django project config (settings/urls/wsgi/asgi)
  settings/
    base.py         shared settings
    dev.py          local dev (SQLite, DEBUG=True)
    production.py   production (Postgres via DATABASE_URL, whitenoise)
theme/              django-tailwind app — edit theme/static_src/src/styles.css
                    for design tokens / global styles
core/               shared nav context processor
home/               HomePage model + template (hero + featured projects)
projects/           ProjectIndexPage + ProjectPage models + templates
about/              AboutPage model + template
contact/            ContactPage (Wagtail form builder) + templates
templates/          base.html + includes/ (button, badge partials)
```

## Design system

Colors and radius live as CSS variables in
`theme/static_src/src/styles.css`, using the same variable names shadcn/ui
uses (`--background`, `--primary`, `--border`, etc.) mapped to Tailwind
utilities via `@theme inline`. Change the values there to retheme the whole
site.

## Deployment

Hosting isn't decided yet. `config/settings/production.py` is host-agnostic:
set `SECRET_KEY`, `ALLOWED_HOSTS`, `DATABASE_URL` (Postgres), and
`CSRF_TRUSTED_ORIGINS` as environment variables, then:

```bash
DJANGO_SETTINGS_MODULE=config.settings.production uv run python manage.py migrate
DJANGO_SETTINGS_MODULE=config.settings.production uv run python manage.py collectstatic
DJANGO_SETTINGS_MODULE=config.settings.production uv run python manage.py tailwind build
```
