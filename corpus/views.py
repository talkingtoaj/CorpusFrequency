import csv

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from corpus.forms import CorpusForm, UploadForm
from corpus.models import MAX_N, PAGE_SIZE, Corpus, Ngram
from corpus.services import ngrams as ngram_service
from corpus.services import scoring as scoring_service
from corpus.services import search as search_service
from corpus.services.extract import UnsupportedDocument
from corpus.services.ingest import add_document


def owned(request, pk):
    """Fetch a corpus, 404ing if it is not this user's.

    Ownership is enforced in the lookup rather than afterwards so that a
    missing corpus and someone else's corpus are indistinguishable.
    """
    return get_object_or_404(Corpus, pk=pk, owner=request.user)


def owned_ngram(request, pk):
    return get_object_or_404(Ngram, pk=pk, corpus__owner=request.user)


@login_required
def corpus_list(request):
    if request.method == "POST":
        form = CorpusForm(request.POST, owner=request.user)
        if form.is_valid():
            corpus = form.save(commit=False)
            corpus.owner = request.user
            corpus.save()
            messages.success(request, f"Created corpus '{corpus.name}'.")
            return redirect("corpus-detail", pk=corpus.pk)
    else:
        form = CorpusForm(owner=request.user)

    corpora = (
        Corpus.objects.filter(owner=request.user)
        .annotate(
            document_count=Count("documents", distinct=True),
            selected_count=Count("ngrams", filter=Q(ngrams__selected=True), distinct=True),
        )
    )
    return render(request, "corpus/corpus_list.html", {"corpora": corpora, "form": form})


@login_required
def corpus_detail(request, pk):
    corpus = owned(request, pk)
    counts = {
        n: corpus.ngrams.filter(n=n).count() for n in range(1, MAX_N + 1)
    }
    return render(
        request,
        "corpus/corpus_detail.html",
        {
            "corpus": corpus,
            "documents": corpus.documents.all(),
            "upload_form": UploadForm(),
            "counts": counts,
            "needs_description_count": corpus.ngrams.filter(
                selected=True, chosen_text=""
            ).count(),
        },
    )


@login_required
@require_POST
def upload_documents(request, pk):
    corpus = owned(request, pk)
    form = UploadForm(request.POST, request.FILES)
    if not form.is_valid():
        for error in form.errors.get("files", ["Choose at least one file to upload."]):
            messages.error(request, error)
        return redirect("corpus-detail", pk=corpus.pk)

    added, rejected = 0, []
    for upload in form.cleaned_data["files"]:
        try:
            add_document(corpus, upload.name, upload.read())
            added += 1
        except UnsupportedDocument as error:
            rejected.append(str(error))

    if added:
        # Counts are now out of date; corpus.is_stale surfaces that in the
        # UI rather than silently serving stale n-grams.
        messages.success(request, f"Added {added} document(s). Re-analyse to update n-grams.")
    for problem in rejected:
        messages.error(request, problem)
    return redirect("corpus-detail", pk=corpus.pk)


@login_required
@require_POST
def analyse(request, pk):
    corpus = owned(request, pk)
    result = ngram_service.rebuild(corpus)
    messages.success(
        request,
        "Analysis complete: {created} new, {updated} updated, {removed} dropped. "
        "Existing selections were kept.".format(**result),
    )
    # Counts have moved, so any importance scores derived from them are now
    # stale. Rescoring here keeps the two from ever disagreeing.
    scored = scoring_service.rescore(corpus)
    if scored["scored"]:
        messages.success(
            request,
            f"Scored {scored['scored']} n-grams against '{corpus.control_corpus.name}'.",
        )
    return redirect("corpus-detail", pk=corpus.pk)


@login_required
def corpus_edit(request, pk):
    corpus = owned(request, pk)
    if request.method == "POST":
        form = CorpusForm(request.POST, instance=corpus, owner=request.user)
        if form.is_valid():
            form.save()
            # Changing the control corpus changes what importance means, so
            # never leave the previous ranking in place.
            scoring_service.rescore(corpus)
            messages.success(request, "Corpus updated.")
            return redirect("corpus-detail", pk=corpus.pk)
    else:
        form = CorpusForm(instance=corpus, owner=request.user)
    return render(request, "corpus/corpus_edit.html", {"corpus": corpus, "form": form})


def filtered(corpus, entries, query):
    """Narrow `entries` to n-grams containing `query`.

    The query is folded with the corpus's language before matching, so
    searching 'istanbul', 'İstanbul' or 'İSTANBUL' all find the same
    n-gram. A database-level case-insensitive match could not do this - it
    does not know that Turkish 'I' lowercases to dotless 'ı'.
    """
    if not query:
        return entries
    return entries.filter(key__contains=corpus.fold(query))


def paginate(request, entries):
    """Page `entries`, clamping an out-of-range page rather than 404ing."""
    paginator = Paginator(entries, PAGE_SIZE)
    return paginator.get_page(request.GET.get("page"))


@login_required
def ngram_list(request, pk, n):
    corpus = owned(request, pk)
    ordering = "-importance" if request.GET.get("by") == "importance" else "-count"
    query = request.GET.get("q", "").strip()

    entries = corpus.ngrams.filter(n=n)
    if ordering == "-importance":
        entries = entries.exclude(importance=None)
    entries = filtered(corpus, entries, query).order_by(ordering, "key")

    return render(
        request,
        "corpus/ngram_list.html",
        {
            "corpus": corpus,
            "n": n,
            "page_obj": paginate(request, entries),
            "total": entries.count(),
            "ordering": ordering,
            "query": query,
        },
    )


@login_required
def ngram_detail(request, pk):
    ngram = owned_ngram(request, pk)
    return render(
        request,
        "corpus/ngram_detail.html",
        {
            "corpus": ngram.corpus,
            "ngram": ngram,
            "results": search_service.search(ngram.corpus, ngram.display),
        },
    )


@login_required
@require_POST
def toggle_selected(request, pk):
    ngram = owned_ngram(request, pk)
    ngram.selected = request.POST.get("selected") == "true"
    ngram.save(update_fields=["selected"])
    return JsonResponse({"selected": ngram.selected})


@login_required
@require_POST
def save_text(request, pk):
    ngram = owned_ngram(request, pk)
    ngram.chosen_text = request.POST.get("chosen_text", "")
    # Choosing an example necessarily means keeping the n-gram. Clearing
    # the text is not the same as dropping it, so selection is never
    # switched off here - only by the checkbox.
    if ngram.chosen_text:
        ngram.selected = True
    ngram.save(update_fields=["chosen_text", "selected"])
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"selected": ngram.selected})
    return redirect("ngram-detail", pk=ngram.pk)


@login_required
def needs_description(request, pk):
    """Issue #8: selections that still have no example sentence."""
    corpus = owned(request, pk)
    query = request.GET.get("q", "").strip()
    entries = filtered(
        corpus, corpus.ngrams.filter(selected=True, chosen_text=""), query
    ).order_by("n", "-count")
    return render(
        request,
        "corpus/needs_description.html",
        {
            "corpus": corpus,
            "page_obj": paginate(request, entries),
            "total": entries.count(),
            "query": query,
        },
    )


@login_required
def export(request, pk):
    corpus = owned(request, pk)
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{corpus.name}-sentences.csv"'
    writer = csv.writer(response)
    writer.writerow(["n", "ngram", "count", "importance", "sentence"])
    for ngram in corpus.ngrams.filter(selected=True).order_by("n", "-count"):
        writer.writerow(
            [ngram.n, ngram.display, ngram.count, ngram.importance or "", ngram.chosen_text]
        )
    return response
