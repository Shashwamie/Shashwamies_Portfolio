import calendar

from django.core.exceptions import ValidationError
from django.db import models
from wagtail import blocks
from wagtail.admin.panels import FieldPanel, FieldRowPanel
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Page
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet


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
    subpage_types = ["about.TimelinePage"]
    max_count = 1


class TimelineEvent(models.Model):
    EVENT_TYPE_CHOICES = [
        ("work", "Work"),
        ("education", "Education"),
    ]
    MONTH_CHOICES = [(i, calendar.month_name[i]) for i in range(1, 13)]

    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES)
    organization = models.CharField(
        max_length=255, help_text="Name of the company or school."
    )
    description = models.TextField(blank=True, help_text="Short description.")
    start_month = models.PositiveSmallIntegerField(choices=MONTH_CHOICES)
    start_year = models.PositiveIntegerField()
    end_month = models.PositiveSmallIntegerField(
        choices=MONTH_CHOICES, null=True, blank=True
    )
    end_year = models.PositiveIntegerField(
        null=True, blank=True, help_text="Leave both end fields blank if this is ongoing."
    )

    panels = [
        FieldPanel("event_type"),
        FieldPanel("organization"),
        FieldPanel("description"),
        FieldRowPanel([FieldPanel("start_month"), FieldPanel("start_year")]),
        FieldRowPanel([FieldPanel("end_month"), FieldPanel("end_year")]),
    ]

    class Meta:
        ordering = ["-start_year", "-start_month"]

    def __str__(self):
        return f"{self.organization} ({self.start_year})"

    def clean(self):
        super().clean()
        if bool(self.end_month) != bool(self.end_year):
            raise ValidationError(
                "Set both an end month and end year, or leave both blank for an ongoing entry."
            )

    def _month_year(self, month, year):
        if not month:
            return str(year)
        return f"{calendar.month_abbr[month]} {year}"

    @property
    def duration_display(self):
        start = self._month_year(self.start_month, self.start_year)
        if not self.end_year:
            return f"{start} – Present"
        end = self._month_year(self.end_month, self.end_year)
        if start == end:
            return start
        return f"{start} – {end}"


class TimelineEventViewSet(SnippetViewSet):
    model = TimelineEvent
    icon = "date"
    list_display = ["organization", "event_type", "start_year", "end_year"]
    list_filter = ["event_type"]


register_snippet(TimelineEventViewSet)


class TimelinePage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]

    parent_page_types = ["about.AboutPage"]
    subpage_types = []
    max_count = 1

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["events"] = TimelineEvent.objects.all()
        return context
