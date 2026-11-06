from django.shortcuts import redirect, render
from django.utils import timezone

from .forms import ReviewForm
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


def review_create(request):
    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            # append змінює той самий список, що імпортований у store, тому
            # review_list побачить запис. REVIEWS = REVIEWS + [...] створив би новий.
            REVIEWS.append({**form.cleaned_data, "created_at": timezone.now()})
            # Redirect після POST: F5 на сторінці списку повторить GET, а не POST.
            return redirect("reviews:review_list")
    else:
        form = ReviewForm()
    # GET або невалідний POST: той самий шаблон, у другому випадку з помилками, статус 200.
    return render(request, "reviews/review_form.html", {"form": form})
