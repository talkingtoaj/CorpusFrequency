"""Turn an uploaded file into Document and Sentence rows."""

from django.db import transaction

from corpus.models import Document, Sentence
from corpus.services import extract
from corpus.services.tokenize import sentences as split_sentences


@transaction.atomic
def add_document(corpus, filename, data):
    """Store the text of one uploaded file against `corpus`.

    The original file is not retained - only its extracted text, which is
    all the analysis needs and avoids holding users' source documents.
    """
    text = extract.extract(filename, data)
    document = Document.objects.create(corpus=corpus, filename=filename, text=text)
    Sentence.objects.bulk_create(
        [
            Sentence(
                document=document,
                text=sentence,
                folded_text=corpus.fold_preserving_length(sentence),
            )
            for sentence in split_sentences(text)
        ]
    )
    return document
