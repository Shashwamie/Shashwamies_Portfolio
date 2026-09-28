# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

A personal portfolio site: Django + Wagtail CMS backend, server-rendered
templates styled with Tailwind CSS v4 using a shadcn/ui-inspired design-token
system (dark, cyberpunk-leaning, neon-yellow primary + sky-blue accent, a
dot-grid background that fades to black toward the bottom of the page).
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
- `about.TimelinePage` (child of `AboutPage`, `max_count=1`,
  `/about/timeline/`) — a vertical branching timeline of school/work history.
  Its entries (`about.TimelineEvent`) are **Wagtail Snippets**, not child
  Pages or a StreamField — the only snippet model in the project so far.
  Snippets get their own admin list (via a `SnippetViewSet`, not the page
  tree) and don't have individual URLs; `TimelinePage.get_context()` just
  queries `TimelineEvent.objects.all()`, already ordered most-recent-first
  via `Meta.ordering`. The template alternates sides with Django's built-in
  `{% cycle %}` tag — no "side" field or Python placement logic. Reach for
  Snippets (over a child-Page or StreamField pattern) for future content
  that's a repeatable structured record without its own page/URL.
- `about.Hobby` — a second Snippet model (see `TimelineEvent` above for the
  general pattern), rendered on `AboutPage` as an interactive "booster pack"
  the visitor drags open to reveal 3 randomly-drawn cards. Each Hobby has a
  fixed `icon` choice (rendered via `templates/includes/hobby_icon.html`,
  one custom inline-SVG `{% if %}` branch per key — a brand-new hobby *type*
  needs a matching choice + SVG branch there, not just a new snippet row)
  and a `rarity` tier (`common`/`uncommon`/`rare`/`legendary`) that drives
  the card-front border/glow/icon color via a `--rarity-color` CSS custom
  property (`data-rarity="..."` on `.hobby-card`, see styles.css). All
  Hobby rows render server-side into the page (hidden); `about_page.html`'s
  inline JS draws 3 per "rip" client-side (weighted by rarity, without
  replacement — see `RARITY_WEIGHTS` in that script, so rarity affects odds
  as well as looks), so re-opening the pack draws a new random set without
  a page reload. Odds depend on how many Hobby rows share each tier, not
  just the weights: adding a new legendary raises the chance of pulling
  *some* legendary. A "Show all hobbies" button (`data-hobby-show-all`,
  below the pack/cards) skips the draw: `dealAllCards()` deals every card
  sorted rarest-first and auto-flips them face-up. All deal/flip/tear
  `setTimeout`s go through `pendingTimers` and are cancelled by
  `clearTable()`, so switching views mid-animation (e.g. "Show all"
  clicked mid-tear) can't be overwritten by a stale callback — route any
  new delayed callback there too.
  Card backs are identical for every hobby (no hobby-specific markup) so
  the back never hints at what's inside — only the flipped front does.

`HomePage.get_context()` pulls featured projects by querying
`projects.models.ProjectPage` directly (imported inside the method to avoid
a circular import with `projects.models`, which doesn't import `home`).

`ProjectPage` also has an optional `background_image` (+
`background_overlay_opacity`, 0–100) that replaces the site's default
dot-grid background for that page only — see the `body_style` block in
Templates below for how that's wired up.

### Templates

Wagtail resolves a page's template by convention:
`<app_label>/templates/<app_label>/<model_name_snake_case>.html`
(e.g. `projects/templates/projects/project_page.html`). The form builder's
post-submit view additionally needs `<app_label>/<model_name>_landing.html`
(`contact/templates/contact/contact_page_landing.html`).

Shared chrome lives in root-level `templates/base.html` (nav + footer) and
`templates/includes/{button,badge,timeline_event}.html` (parameter-driven
includes, e.g.
`{% include "includes/button.html" with href=... text=... variant="primary" %}`).
Project templates `{% extends "base.html" %}`.

The top nav is data-driven off `core/context_processors.py`'s `nav_pages`
(the site root's live, `show_in_menus=True` children) — new top-level pages
appear automatically once published with "Show in menus" checked. Each of
those nav items is a click-to-open dropdown (vanilla JS in `base.html`,
`data-dropdown`/`data-dropdown-trigger`/`data-dropdown-panel` attribute
hooks — no framework); dropdown *contents* are currently hardcoded
placeholder links per item, **except** About's, which links to the real
Timeline page via a dedicated `timeline_page` context var (also from
`nav_pages()`) rather than a generic "list all children" mechanism — Projects'
children are individual `ProjectPage`s that must not flood its dropdown.
Mobile reuses native `<details>`/`<summary>` accordions instead of the JS
dropdown (no hover on touch).

`base.html`'s `<body>` tag has an empty `{% block body_style %}{% endblock %}`
hook. Pages normally leave it empty (falls back to the default dot-grid
`body` background from `styles.css`); `project_page.html` fills it with an
inline `style="background-image: ..."` when `page.background_image` is set.
This is the pattern to reuse for any future per-page background override.

### Design system / Tailwind

Tailwind v4, CSS-first config (no `tailwind.config.js`) — everything lives
in `theme/static_src/src/styles.css`: shadcn-style CSS variables
(`--background`, `--primary`, `--border`, etc.) defined under `:root`,
mapped to Tailwind utilities via `@theme inline`. Retheme the whole site by
editing the variable values there. Note `--secondary` and `--accent` are no
longer aliased to the same value (they were originally) — `--accent` is the
sky-blue token actually used for accents/badges; `--secondary` has since
been tuned to a near-neutral gray. Compiled output
(`theme/static/css/dist/styles.css`) is gitignored and built by
`manage.py tailwind {install,start,dev,build}`; templates pull it in via
`{% load tailwind_tags %}{% tailwind_css %}` in `base.html`.

`tailwind dev` shells out to `honcho` (a project dependency) using the
generated `Procfile.tailwind` to run the Django server and the Tailwind
watcher together.

**`clip-path` + `box-shadow`/`filter` gotcha:** buttons use a `.clip-corner`
utility (chamfers the bottom-right corner via `clip-path`) for the
cyberpunk-panel look. `clip-path` clips *everything* an element paints,
including its own `box-shadow` — so a neon "glow" can't just be `box-shadow`
on the same clipped element (it silently disappears). Two glow utilities
exist for this: `.glow-primary` uses `filter: drop-shadow(...)` and is only
safe on elements *without* `clip-corner` (Safari has had bugs clipping
`drop-shadow` output too, matching `box-shadow`'s issue, when both are on
the same element). `.glow-primary-clip` is `box-shadow` + `border-radius` on
an *unclipped wrapper* around the clipped shape — see
`templates/includes/button.html` for the two-layer markup this requires.
Don't reach for a single-element `box-shadow`/`filter` glow on anything that
also has `clip-corner`.

### First `@keyframes` in the project

The hobby-card pack (`about_page.html` + the `.hobby-card*`/`.hobby-pack*`
rules in `styles.css`) introduced this project's first CSS `@keyframes`
(`hobby-card-wiggle` on hover, `hobby-card-deal` for the staggered
deal-in, `hobby-card-shimmer` reused for both the legendary-rarity card foil
sweep and the closed pack's holo-foil sheen). The card flip itself is a 3D
transform (`transform-style: preserve-3d` + `backface-visibility: hidden`
on `.hobby-card-inner`/`-front`/`-back`), not a keyframe animation.

The pack's look went through several iterations before landing on
deliberately flat/bold — worth knowing before "improving" it again. CSS
divs can't produce real photorealistic 3D/foil rendering: an early attempt
combined gradients + shimmer + a mouse-driven `perspective`/`rotateX`/
`rotateY` tilt + a radial glow flash all at once, chasing a "realistic
foil pack" look, and it just read as flat shapes pretending to be 3D
(worse than embracing flat) plus, later, a jarring wash of color. Both the
mouse-tilt (`hobby-pack-tilt`) and a restrained shine sweep
(`.hobby-pack-body::after`, reusing the same diagonal-highlight technique
as the legendary-card shimmer) were reintroduced afterward, on request,
*on their own* — each is a small, isolated touch layered onto the flat
solid-color base (`border-primary`/`bg-accent` fills), not a return to the
combined "realistic foil" treatment. If asked to make the pack look more
"realistic/3D" or "foil-like" as a general direction again, raise that
tradeoff before spending effort on it — CSS still won't get there, and the
combined version already didn't land — but a specific, narrow, tasteful
addition (like the tilt or the shimmer) is fine to just build, the way
those two were.

Structurally it's two pieces: a static, always-fully-visible
`[data-hobby-pack-body]` and a `[data-hobby-pack-lid]` cap raised above it
(`top: -42px` in the template, so it's a genuinely separate floating piece,
not overlapping the body) — same shape/material as the body (solid
`bg-card` + `border-primary`), not a differently-colored strip. The lid is
the *only* piece that ever moves; the body never animates except fading
out once the lid's gone. Two earlier versions of this mechanic didn't work
out, both instructive if this gets revisited: (1) making the *entire* pack
a single peelable "lid" (scratch-card-style, wiping the whole face away as
you dragged) looked wrong — real foil packs only lose a small piece up
top, the bulk stays intact until opened; (2) a spiky `clip-path` "crimp"
strip for that top piece looked like "a zigzag sticker pasted onto a flat
rectangle" rather than an integrated part of the pack. The current version
drops the zigzag/tear-line idea entirely in favor of an "open seam" look:
`.hobby-pack-body` has `border-top-color: transparent` and a
bottom-only `border-radius`, `.hobby-pack-lid` has `border-bottom-color:
transparent` and a top-only `border-radius` — so at rest, with the lid
sitting just above the body, their matching side borders line up into one
continuous silhouette and the transparent top/bottom edges read as the
seam between them, rather than needing a fake torn edge. A glow line
(`.hobby-pack-lid::after`) with a bright spot sweeping left → right along the
lid's side of that seam (`hobby-pack-lid-sweep`, same direction as the drag) to
hint it's the part you pull. The lid also rests slightly rotated
(`translateY(-5px) rotate(3deg)`, see `.hobby-pack-lid` in styles.css) so
it doesn't look perfectly seated even before you touch it. Dragging just
slides that same offset further out; there's no "reveal" or "tear" to
fake, only a rigid piece coming further loose and eventually flying off.
This is also why the mechanic is simple JS (`setLidProgress` is a couple
of `translate`/`rotate` values) instead of the clip-path-polygon math the
zigzag version needed.

Plain JS (`pointerdown`/`pointermove`/`pointerup`, Pointer Events cover
mouse + touch in one code path): dragging tracks the pointer's *absolute*
x position across the pack's width (not delta from drag-start — progress
should track where the cursor physically is) and sets the lid's
`transform` directly each move, with `lid.style.transition = "none"` for
1:1 tracking while actively dragging. Releasing before the ~85% threshold
clears that inline `transform`/`transition` override, letting the
`.hobby-pack-lid` CSS rule's own transition ease it back to the resting
"ajar" position — a plain `transform` transition works fine here (unlike
the old clip-path version, a `translate`/`rotate` interpolates smoothly no
matter the start/end values, no point-count mismatch to work around).
Crossing the threshold instead adds `.hobby-pack.is-torn`, which flings
the lid further off (its own transform in that state, glowing seam-line
included since it's a pseudo-element on the same fading/moving lid)
followed shortly by the body fading out, before the pack is hidden and
cards are dealt. The lid rotates clockwise (positive degrees — left edge
up, right edge down) throughout `setLidProgress` as drag progress
increases — the `is-torn` end transform must keep rotating the same
direction (just further, e.g. `85deg`), not
flip to a negative value: an earlier version had the drag phase and the
`is-torn` CSS disagree on sign, which snapped the rotation direction
visibly mid-flight instead of reading as one continuous motion.

The tear also triggers mid-drag as soon as the threshold is crossed, not on
release: gating on the release position let users' natural
overshoot-then-ease-back motion undershoot the threshold and require
several attempts (this was also true of an even earlier version of the
pack that split into two halves and dragged apart horizontally).

**`data-hobby-pack-*` attribute vs. `.hobby-pack-*` class — both are
needed, on purpose.** Elements here always carry two separate hooks: a
`data-hobby-pack-lid`-style attribute (what JS's `querySelector` targets)
and a `hobby-pack-lid`-style *class* (what `styles.css`'s `.hobby-pack.is-torn
.hobby-pack-lid { ... }` selectors target). These are easy to conflate
since they're spelled almost the same, and for a while several elements
here — the pack container itself, and `[data-hobby-pack-body]` — only had
the `data-*` attribute and not the matching class. JS still worked fine
(it only ever used the attribute selector), so the drag itself looked
correct in every test; but every CSS rule keyed off `.hobby-pack.is-torn`
silently never matched, so the *completion* animations (lid flinging the
rest of the way off, body fading out, and — at the time — a scattered-particle
"fizzle" burst that was added then later removed again in favor of a plain
fade, see the comment above `.hobby-pack-body` in styles.css) never
ran — the pack would just sit there doing nothing for the full timeout,
then instantly get `hidden` added by the unconditional `setTimeout` in
`completeTear()`, which masked the bug because the end result (cards
appear) still looked right. This went unnoticed through several rounds of
screenshot-based verification because screenshots taken during the *drag*
phase (JS-driven, correct) or *after* the hide (also correct, just via the
unconditional timeout) both looked fine — only a mid-completion frame or a
direct `getComputedStyle` check exposed it. If a new `.hobby-pack-*` piece
gets added, verify with `getComputedStyle(el).animationName` /
`.transform` /`.opacity` at a specific mid-transition timestamp, not just
screenshots at the start and end.
