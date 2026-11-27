from django.conf import settings
from django.db import models


class ReviewRequest(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        IN_REVIEW = "in_review", "In review"
        CLOSED = "closed", "Closed"

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="authored_requests",
    )
    # Порожній, доки рев'юер не візьме запит (claim, День 10). Індекс для FK Django
    # створює сам, db_index=True не потрібен.
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_requests",
    )
    title = models.CharField(max_length=200)
    course_url = models.URLField()
    # Без null=True: для текстових полів "немає значення" — це "", а не NULL.
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=32, choices=Status.choices, default=Status.OPEN, db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["author", "title"], name="uniq_review_request_author_title"
            )
        ]

    def __str__(self):
        return self.title


class Comment(models.Model):
    # Саме review_request: День 5 фільтрує ?review_request=<id>, День 8 будує
    # UniqueConstraint(fields=["review_request", "to_status"]).
    review_request = models.ForeignKey(
        ReviewRequest, on_delete=models.CASCADE, related_name="comments"
    )
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.author} on #{self.review_request_id}"
