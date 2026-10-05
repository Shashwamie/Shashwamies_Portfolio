from django.db import models
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel, FieldRowPanel, InlinePanel, MultiFieldPanel
from wagtail.contrib.forms.models import AbstractEmailForm, AbstractFormField
from wagtail.fields import RichTextField


class ContactFormField(AbstractFormField):
    page = ParentalKey(
        "ContactPage", on_delete=models.CASCADE, related_name="form_fields"
    )


class ContactPage(AbstractEmailForm):
    intro = RichTextField(blank=True)
    contact_email = models.EmailField(
        blank=True, help_text="Shown above the form as a direct way to reach you."
    )
    linkedin_url = models.URLField(
        "LinkedIn URL",
        blank=True,
        help_text="Full profile URL, e.g. https://www.linkedin.com/in/your-name/",
    )
    thank_you_text = RichTextField(blank=True)

    content_panels = AbstractEmailForm.content_panels + [
        FieldPanel("intro"),
        MultiFieldPanel(
            [FieldPanel("contact_email"), FieldPanel("linkedin_url")],
            heading="Direct contact",
        ),
        InlinePanel("form_fields", label="Form fields"),
        FieldPanel("thank_you_text"),
        MultiFieldPanel(
            [
                FieldRowPanel(
                    [FieldPanel("from_address"), FieldPanel("to_address")]
                ),
                FieldPanel("subject"),
            ],
            heading="Email notification",
        ),
    ]

    parent_page_types = ["home.HomePage"]
    subpage_types = []
    max_count = 1

    @property
    def linkedin_display(self):
        """The LinkedIn URL without scheme/www/trailing slash, for display."""
        url = self.linkedin_url.split("://", 1)[-1]
        if url.startswith("www."):
            url = url[len("www."):]
        return url.rstrip("/")
