from django import forms


class ReviewForm(forms.Form):
    title = forms.CharField(max_length=200)
    author = forms.CharField(max_length=100)
    rating = forms.IntegerField(min_value=1, max_value=5)
    body = forms.CharField(widget=forms.Textarea)

    def clean_title(self):
        # CharField уже обрізає пробіли сам (strip=True за замовчуванням). Явний strip()
        # лишає перевірку довжини правильною, навіть якщо поле отримає strip=False.
        title = self.cleaned_data["title"].strip()
        if len(title) < 3:
            raise forms.ValidationError("Title must be at least 3 characters long.")
        return title

    def clean(self):
        cleaned_data = super().clean()
        rating = cleaned_data.get("rating")
        body = cleaned_data.get("body")
        # Поле, що не пройшло власну валідацію, відсутнє в cleaned_data: тоді
        # міжполеве правило не перевіряємо, помилка для нього вже є.
        if rating is not None and body is not None and rating <= 2 and len(body) < 20:
            self.add_error("body", "A rating of 2 or lower needs at least 20 characters.")
        return cleaned_data
