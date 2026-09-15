# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

A personal portfolio site: Django + Wagtail CMS backend, server-rendered
templates styled with Tailwind CSS v4 using a shadcn/ui-inspired design-token
system (dark, cyberpunk-leaning, magenta/purple primary + cyan secondary).
No React/frontend framework — Wagtail pages render directly to HTML/Tailwind.
Python deps are managed with `uv`; hosting/production database are not yet
decided (see `config/settings/production.py`).

## Commands

All Python commands run through `uv run` so they use the project venv.

```bash
# Setup
uv sync                                          # install Python deps
uv run python manage.py tailwind install         # install Tailwind's npm deps
uv run python manage.py migrate
uv run python manage.py createsuperuser

# Local dev (runs Django dev server + Tailwind watcher together via honcho)
uv run python manage.py tailwind dev
# equivalent two-terminal alternative:
#   uv run python manage.py runserver
#   uv run python manage.py tailwind start

# After changing models
uv run python manage.py makemigrations <app>
uv run python manage.py migrate

# Tests (Django's runner; no tests written yet — app tests.py files are stubs)
uv run python manage.py test
uv run python manage.py test projects              # single app
uv run python manage.py test projects.tests.SomeTestCase.test_thing   # single test

# Tailwind CSS production build (no watch)
uv run python manage.py tailwind build

# Production-settings commands (see Settings below for why DJANGO_SETTINGS_MODULE is needed)
DJANGO_SETTINGS_MODULE=config.settings.production uv run python manage.py migrate
DJANGO_SETTINGS_MODULE=config.settings.production uv run python manage.py collectstatic
```

Site URLs when running locally: `/` (site), `/cms/` (Wagtail admin — content
editing), `/django-admin/` (Django admin — users/groups).

## Architecture

### Settings split — asymmetric defaults

`config/settings/{base,dev,production}.py`. `dev.py` sets `DEBUG=True` and
SQLite; `production.py` reads `DATABASE_URL`/`ALLOWED_HOSTS`/etc. from env
vars (via `dj-database-url`, `python-dotenv`) and defaults to whitenoise +
`CompressedManifestStaticFilesStorage`.

**`manage.py` defaults to `config.settings.dev`**, but **`wsgi.py`/`asgi.py`
default to `config.settings.production`** (fail-closed for real deployments).
This means `manage.py` commands run fine with no env var set, but anything
going through wsgi/asgi needs `DJANGO_SETTINGS_MODULE` set explicitly if you
want dev settings, and production commands invoked via `manage.py` (like
`collectstatic` above) need it set explicitly too.

### Content model (Wagtail page tree)

Apps: `home`, `projects`, `about`, `contact`, plus `core` (shared, no
models — just the nav context processor) and `theme` (django-tailwind's
generated app, holds the Tailwind source/build).

Page tree is enforced via each model's `parent_page_types`/`subpage_types`:

- `home.HomePage` — the site root (Wagtail `Site.root_page`), `max_count=1`.
  `subpage_types` is explicitly `[projects.ProjectIndexPage, about.AboutPage,
  contact.ContactPage]` — adding a new top-level page type means adding it
  here too, or Wagtail's admin won't offer it as a child of Home.
- `projects.ProjectIndexPage` (child of Home, `max_count=1`) → lists its
  child `ProjectPage`s; supports `?tag=<name>` filtering via
  `get_context()`.
- `projects.ProjectPage` — the main content-editing surface. Notable fields:
  `tech_stack` is a `ClusterTaggableManager` (django-taggit via
  modelcluster), rendered as badges and used for the tag filter; `body` is a
  `StreamField` with `paragraph`/`image`/`code` block types; `featured`
  (bool) controls whether it shows in Home's "Featured projects" section.
- `about.AboutPage`, `contact.ContactPage` — both children of Home,
  `max_count=1`. `ContactPage` is Wagtail's form-builder pattern
  (`AbstractEmailForm` + `AbstractFormField`/`ContactFormField`) — form
  fields (name/email/message) are admin-editable, not hardcoded.

`HomePage.get_context()` pulls featured projects by querying
`projects.models.ProjectPage` directly (imported inside the method to avoid
a circular import with `projects.models`, which doesn't import `home`).

### Templates

Wagtail resolves a page's template by convention:
`<app_label>/templates/<app_label>/<model_name_snake_case>.html`
(e.g. `projects/templates/projects/project_page.html`). The form builder's
post-submit view additionally needs `<app_label>/<model_name>_landing.html`
(`contact/templates/contact/contact_page_landing.html`).

Shared chrome lives in root-level `templates/base.html` (nav + footer) and
`templates/includes/{button,card... }.html` (parameter-driven includes, e.g.
`{% include "includes/button.html" with href=... text=... variant="primary" %}`).
Project templates `{% extends "base.html" %}`.

The nav is data-driven: `core/context_processors.py`'s `nav_pages` context
processor exposes the site root's live, `show_in_menus=True` children as
`nav_pages` — new top-level pages appear in nav automatically once published
with "Show in menus" checked, no template changes needed.

### Design system / Tailwind

Tailwind v4, CSS-first config (no `tailwind.config.js`) — everything lives
in `theme/static_src/src/styles.css`: shadcn-style CSS variables
(`--background`, `--primary`, `--border`, etc.) defined under `:root`,
mapped to Tailwind utilities via `@theme inline`. Retheme the whole site by
editing the variable values there. Compiled output
(`theme/static/css/dist/styles.css`) is gitignored and built by
`manage.py tailwind {install,start,dev,build}`; templates pull it in via
`{% load tailwind_tags %}{% tailwind_css %}` in `base.html`.

`tailwind dev` shells out to `honcho` (a project dependency) using the
generated `Procfile.tailwind` to run the Django server and the Tailwind
watcher together.
