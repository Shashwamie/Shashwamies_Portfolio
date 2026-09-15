from wagtail.models import Site


def nav_pages(request):
    """Expose the site's root page and its menu-visible children for site-wide nav."""
    site = Site.find_for_request(request)
    if site is None:
        return {}

    home = site.root_page
    return {
        "nav_home": home,
        "nav_pages": home.get_children().live().in_menu(),
    }
