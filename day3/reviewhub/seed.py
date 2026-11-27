"""Тестові дані: python3 manage.py shell < seed.py

Щоразу починає з чистого аркуша: видаляє всі ReviewRequest (коментарі йдуть слідом
через CASCADE) і створює 60 запитів та 300 коментарів заново. Користувачів
user0..user4 створює, лише якщо їх ще немає.
"""

from django.contrib.auth import get_user_model

from reviews.models import Comment, ReviewRequest

User = get_user_model()

# create_user без пароля ставить непридатний пароль: увійти цими користувачами не можна.
users = [
    User.objects.filter(username=name).first() or User.objects.create_user(name)
    for name in (f"user{i}" for i in range(5))
]

ReviewRequest.objects.all().delete()

# На Postgres bulk_create повертає об'єкти з id (INSERT … RETURNING), тож на них
# одразу можна посилатися з коментарів.
review_requests = ReviewRequest.objects.bulk_create(
    ReviewRequest(
        author=users[i % 5],
        title=f"Course review #{i:02d}",
        course_url=f"https://courses.example.com/c/{i}/",
        description=f"Please review lesson {i % 12 + 1}.",
    )
    for i in range(60)
)

Comment.objects.bulk_create(
    Comment(
        review_request=rr,
        author=users[(i + k) % 5],
        body=f"Comment {k + 1} on {rr.title}",
    )
    for i, rr in enumerate(review_requests)
    for k in range(5)
)

print(
    "users:", User.objects.filter(username__in=[u.username for u in users]).count(),
    "requests:", ReviewRequest.objects.count(),
    "comments:", Comment.objects.count(),
)
