"""Locale-aware case folding for n-gram matching.

`str.lower()` applies Unicode's *default* case mappings, which are
locale-independent and therefore wrong for Turkish and Azeri:

    'İ'.lower()  ->  'i' + U+0307   (two codepoints, not one)
    'I'.lower()  ->  'i'            (Turkish requires dotless 'ı')

The first breaks string matching outright: an n-gram key built by
lowercasing 'İ' can never equal the lowercased corpus text, and the
trailing combining mark confuses regex word boundaries. The second
silently merges words that Turkish considers distinct, since dotted 'i'
and dotless 'ı' are separate letters standing for separate phonemes.

Unicode's SpecialCasing.txt names Turkish/Azeri (and Lithuanian) as the
only languages needing conditional casing for 'i'. Every other language
is served correctly by the default mappings, so one special case plus
normalisation covers the whole corpus, rather than a per-language
alphabet table that has to be hand-maintained for each new language.
"""

import unicodedata

# Languages whose dotted/dotless 'i' distinction the default Unicode case
# mappings get wrong. Mapped before folding so that 'İ' never expands into
# the two-codepoint 'i' + COMBINING DOT ABOVE sequence.
DOTTED_I_LANGUAGES = ("tr", "az")

DOTTED_I_MAP = {
    "İ": "i",  # U+0130 LATIN CAPITAL LETTER I WITH DOT ABOVE
    "I": "ı",  # U+0049 -> U+0131 LATIN SMALL LETTER DOTLESS I
}

DEFAULT_LANGUAGE = "tr"


def convert_to_lower_case(text: str, lang: str = DEFAULT_LANGUAGE) -> str:
    """Return `text` folded to lower case for caseless comparison.

    Uses `str.casefold()` rather than `str.lower()` because casefolding is
    the operation Unicode defines for caseless matching (it also maps, for
    example, German 'ß' to 'ss'). Output is normalised to NFC so that
    corpus text arriving in decomposed form compares equal to composed
    text.
    """
    if lang in DOTTED_I_LANGUAGES:
        for upper, lower in DOTTED_I_MAP.items():
            text = text.replace(upper, lower)
    return unicodedata.normalize("NFC", text.casefold())


def fold_preserving_length(text: str, lang: str = DEFAULT_LANGUAGE) -> str:
    """Fold `text` while guaranteeing a one-to-one codepoint mapping.

    Every character in the result sits at the same index as the character
    it came from, so offsets from a match against the folded string can be
    used to slice the *original* string. Characters whose fold expands to
    more than one codepoint (German 'ß' -> 'ss', the 'ﬁ' ligature) are left
    unfolded rather than break that guarantee.

    Agrees with `convert_to_lower_case` for every folding that is already
    one-to-one, which is the whole Turkish alphabet.
    """
    folded_characters = []
    for character in text:
        folded = convert_to_lower_case(character, lang)
        folded_characters.append(folded if len(folded) == 1 else character)
    return "".join(folded_characters)
