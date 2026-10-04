from django.core.validators import MaxValueValidator, MinValueValidator
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
        # Imported here to match HomePage's pattern of avoiding cross-app
        # imports at module load.
        from about.models import AboutPage

        context = super().get_context(request, *args, **kwargs)
        projects = ProjectPage.objects.child_of(self).live()

        tag = request.GET.get("tag")
        if tag:
            projects = projects.filter(tech_stack__name__iexact=tag)

        # Filter buttons come from the About page's Languages list, so adding
        # a language there adds a button here. Matching a project relies on
        # it having a tech_stack tag with the same name (case-insensitive).
        about_page = AboutPage.objects.live().first()
        languages = []
        if about_page:
            languages = [
                block.value.strip()
                for block in about_page.languages
                if block.value.strip()
            ]
        active_language = next(
            (lang for lang in languages if tag and lang.lower() == tag.lower()),
            None,
        )

        context["projects"] = projects
        context["tag"] = tag
        context["languages"] = languages
        context["active_language"] = active_language
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
    background_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Optional background image shown behind this project's page. Falls back to the site's default background if left blank.",
    )
    background_overlay_opacity = models.PositiveIntegerField(
        default=70,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Darkness of the overlay on top of the background image: 0 = full image, no darkening, 100 = fully dark. Only applies when a background image is set.",
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
        FieldPanel("background_image"),
        FieldPanel("background_overlay_opacity"),
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
