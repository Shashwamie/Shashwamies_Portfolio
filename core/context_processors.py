from wagtail.models import Site


def nav_pages(request):
    """Expose the site's root page and its menu-visible children for site-wide nav."""
    site = Site.find_for_request(request)
    if site is None:
        return {}

    home = site.root_page
    context = {
        "nav_home": home,
        "nav_pages": home.get_children().live().in_menu(),
    }

    # About's Timeline child page gets a direct nav-dropdown link (see
    # templates/base.html) rather than a generic "list all children"
    # mechanism, since e.g. Projects' children are individual project pages
    # that shouldn't flood its dropdown.
    about_page = home.get_children().filter(slug="about").first()
    if about_page:
        context["timeline_page"] = (
            about_page.get_children().live().filter(slug="timeline").first()
        )

    return context
