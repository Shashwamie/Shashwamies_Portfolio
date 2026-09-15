from django.db import models
from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField
from wagtail.models import Page


class HomePage(Page):
    heading = models.CharField(
        max_length=255, blank=True, help_text="Big hero heading, e.g. your name."
    )
    subheading = models.CharField(
        max_length=255, blank=True, help_text="Short role/title line under the heading."
    )
    intro = RichTextField(blank=True, help_text="A few sentences introducing yourself.")
    resume_document = models.ForeignKey(
        "wagtaildocs.Document",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Optional resume/CV file, linked from the homepage.",
    )

    content_panels = Page.content_panels + [
        FieldPanel("heading"),
        FieldPanel("subheading"),
        FieldPanel("intro"),
        FieldPanel("resume_document"),
    ]

    parent_page_types = ["wagtailcore.Page"]
    subpage_types = [
        "projects.ProjectIndexPage",
        "about.AboutPage",
        "contact.ContactPage",
    ]
    max_count = 1

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        from projects.models import ProjectIndexPage, ProjectPage

        context["featured_projects"] = (
            ProjectPage.objects.live()
            .filter(featured=True)
            .order_by("-first_published_at")[:6]
        )
        context["projects_index"] = ProjectIndexPage.objects.live().child_of(self).first()
        return context
