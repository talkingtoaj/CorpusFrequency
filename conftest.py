"""Point the corpus pipeline at the test fixtures.

`read`, `get_ngrams` and `find_sentences` all do their work at import
time, so these have to be set before any test module imports `app`.
pytest loads the root conftest first, which makes this the right place.
"""

import os
import pathlib
import tempfile

FIXTURES = pathlib.Path(__file__).parent / "tests" / "fixtures" / "input_files"

# A fresh directory per run: read.py skips regenerating its output when the
# file already exists, so a reused path would serve a stale corpus.
_scratch = tempfile.mkdtemp(prefix="corpusfrequency-tests-")

os.environ["CORPUS_INPUT_FOLDER"] = str(FIXTURES)
os.environ["CORPUS_OUTPUT_FILE"] = str(pathlib.Path(_scratch) / "output.txt")
os.environ["CORPUS_STATE_FILE"] = str(pathlib.Path(_scratch) / "state")
