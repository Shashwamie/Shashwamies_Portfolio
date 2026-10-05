from django.db import models
from wagtail import blocks
from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Page


class FlipCardBlock(blocks.StructBlock):
    title = blocks.CharBlock(help_text="Shown on the front of the card.")
    teaser = blocks.CharBlock(
        required=False, help_text="Optional short line under the title on the front."
    )
    body = blocks.TextBlock(help_text="Shown on the back once the card is flipped.")
    link_page = blocks.PageChooserBlock(
        required=False, help_text="Optional page linked from the back of the card."
    )
    link_text = blocks.CharBlock(
        required=False, help_text='Label for that link, e.g. "See all projects".'
    )

    class Meta:
        icon = "doc-full"
        label = "Flip card"


class HomePage(Page):
    heading = models.CharField(
        max_length=255, blank=True, help_text="Big hero heading, e.g. your name."
    )
    aka_name = models.CharField(
        max_length=255,
        blank=True,
        help_text='Optional "aka" line shown under the heading, e.g. aka "Shashwamie".',
    )
    subheading = models.CharField(
        max_length=255, blank=True, help_text="Short role/title line under the heading."
    )
    intro = RichTextField(blank=True, help_text="A few sentences introducing yourself.")
    flip_cards = StreamField(
        [("card", FlipCardBlock())],
        blank=True,
        help_text="Cards between the hero and Featured projects that visitors click to flip over.",
    )
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
        FieldPanel("aka_name"),
        FieldPanel("subheading"),
        FieldPanel("intro"),
        FieldPanel("flip_cards"),
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
