from django import forms
from django.conf import settings
from django.template.defaultfilters import filesizeformat

from corpus.models import Corpus
from corpus.services.extract import SUPPORTED_EXTENSIONS


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    """A FileField that keeps every file rather than just the last one."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput(attrs={"multiple": True}))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        if isinstance(data, (list, tuple)):
            return [super(MultipleFileField, self).clean(item, initial) for item in data]
        return [super().clean(data, initial)]


class CorpusForm(forms.ModelForm):
    class Meta:
        model = Corpus
        fields = ["name", "kind", "language", "control_corpus"]
        help_texts = {
            "kind": "A control corpus is general language you compare a target against.",
        }

    def __init__(self, *args, owner=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Only ever offer the user their own control corpora - the dropdown
        # would otherwise expose other people's corpus names.
        queryset = Corpus.objects.none()
        if owner is not None:
            queryset = Corpus.objects.filter(owner=owner, kind=Corpus.CONTROL)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
        self.fields["control_corpus"].queryset = queryset
        self.fields["control_corpus"].required = False
        self.fields["control_corpus"].label = "Score against"


class UploadForm(forms.Form):
    files = MultipleFileField(
        label=f"Documents ({', '.join(SUPPORTED_EXTENSIONS)})",
    )

    def clean_files(self):
        """Reject oversized uploads before anything tries to parse them.

        The cap is about parse cost rather than storage - the source file is
        discarded once its text has been extracted.
        """
        files = self.cleaned_data["files"]
        limit = settings.MAX_UPLOAD_BYTES
        too_big = [upload.name for upload in files if upload.size > limit]
        if too_big:
            raise forms.ValidationError(
                "%(names)s exceed(s) the %(limit)s upload limit.",
                params={"names": ", ".join(too_big), "limit": filesizeformat(limit)},
            )
        return files
