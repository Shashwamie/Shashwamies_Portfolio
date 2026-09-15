from django.db import models
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey
from taggit.models import TaggedItemBase
from wagtail import blocks
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.fields import RichTextField, StreamField
from wagtail.images.blocks import ImageChooserBlock
from wagtail.models import Page


class ProjectIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]

    parent_page_types = ["home.HomePage"]
    subpage_types = ["projects.ProjectPage"]
    max_count = 1

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        projects = ProjectPage.objects.child_of(self).live()

        tag = request.GET.get("tag")
        if tag:
            projects = projects.filter(tech_stack__name__iexact=tag)

        context["projects"] = projects
        context["tag"] = tag
        return context


class ProjectPageTag(TaggedItemBase):
    content_object = ParentalKey(
        "projects.ProjectPage", on_delete=models.CASCADE, related_name="tagged_items"
    )


class ProjectPage(Page):
    summary = models.CharField(
        max_length=300, help_text="Short blurb shown on project cards."
    )
    cover_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    tech_stack = ClusterTaggableManager(through=ProjectPageTag, blank=True)
    body = StreamField(
        [
            ("paragraph", blocks.RichTextBlock()),
            ("image", ImageChooserBlock()),
            ("code", blocks.TextBlock(help_text="Paste a code snippet.")),
        ],
        blank=True,
    )
    github_url = models.URLField(blank=True)
    live_url = models.URLField(blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    featured = models.BooleanField(
        default=False,
        help_text="Show this project in the Featured Projects section on the homepage.",
    )

    content_panels = Page.content_panels + [
        FieldPanel("summary"),
        FieldPanel("cover_image"),
        FieldPanel("tech_stack"),
        FieldPanel("body"),
        MultiFieldPanel(
            [FieldPanel("github_url"), FieldPanel("live_url")],
            heading="Links",
        ),
        MultiFieldPanel(
            [FieldPanel("start_date"), FieldPanel("end_date")],
            heading="Timeline",
        ),
        FieldPanel("featured"),
    ]

    parent_page_types = ["projects.ProjectIndexPage"]
    subpage_types = []

    @property
    def tech_stack_list(self):
        return list(self.tech_stack.names())
