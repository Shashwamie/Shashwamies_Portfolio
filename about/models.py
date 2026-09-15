from django.db import models
from wagtail import blocks
from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Page


class AboutPage(Page):
    photo = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    bio = RichTextField(blank=True)
    skills = StreamField(
        [("skill", blocks.CharBlock(icon="tag"))],
        blank=True,
        help_text="One block per skill/technology, shown as badges.",
    )
    resume_document = models.ForeignKey(
        "wagtaildocs.Document",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    content_panels = Page.content_panels + [
        FieldPanel("photo"),
        FieldPanel("bio"),
        FieldPanel("skills"),
        FieldPanel("resume_document"),
    ]

    parent_page_types = ["home.HomePage"]
    subpage_types = []
    max_count = 1
