from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    # allauth owns /accounts/, including login and logout. The Django admin
    # keeps its own login form, so a superuser can still get in if the OAuth
    # configuration breaks.
    path("accounts/", include("allauth.urls")),
    path("", include("corpus.urls")),
]
