from django.urls import path

from corpus import views

urlpatterns = [
    path("health", views.health, name="health"),
    path("", views.corpus_list, name="corpus-list"),
    path("corpus/<int:pk>/", views.corpus_detail, name="corpus-detail"),
    path("corpus/<int:pk>/edit/", views.corpus_edit, name="corpus-edit"),
    path("corpus/<int:pk>/upload/", views.upload_documents, name="upload-documents"),
    path("corpus/<int:pk>/analyse/", views.analyse, name="analyse"),
    path("corpus/<int:pk>/ngrams/<int:n>/", views.ngram_list, name="ngram-list"),
    path("corpus/<int:pk>/needs-description/", views.needs_description, name="needs-description"),
    path("corpus/<int:pk>/export/", views.export, name="export"),
    path("ngram/<int:pk>/", views.ngram_detail, name="ngram-detail"),
    path("ngram/<int:pk>/select/", views.toggle_selected, name="toggle-selected"),
    path("ngram/<int:pk>/text/", views.save_text, name="save-text"),
]
