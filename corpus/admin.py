from django.contrib import admin

from corpus.models import Corpus, Document, Ngram, Sentence


@admin.register(Corpus)
class CorpusAdmin(admin.ModelAdmin):
    list_display = ["name", "owner", "kind", "language", "analysed_at"]
    list_filter = ["kind", "language"]
    search_fields = ["name", "owner__username"]


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ["filename", "corpus", "uploaded_at"]
    search_fields = ["filename"]


@admin.register(Ngram)
class NgramAdmin(admin.ModelAdmin):
    list_display = ["display", "corpus", "n", "count", "importance", "selected"]
    list_filter = ["n", "selected"]
    search_fields = ["display", "key"]


admin.site.register(Sentence)
