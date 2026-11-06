from django.shortcuts import render

from .store import REVIEWS


def review_list(request):
    # Рахуємо тут, а не в шаблоні: шаблон лише показує готові значення.
    review_count = len(REVIEWS)
    avg_rating = round(sum(r["rating"] for r in REVIEWS) / review_count, 1) if REVIEWS else None
    context = {
        "reviews": REVIEWS,
        "review_count": review_count,
        "avg_rating": avg_rating,
    }
    return render(request, "reviews/review_list.html", context)
