"""Sample Turkish text the analysis is exercised against.

'İstanbul' appears in three casings that must merge into one n-gram, and
'Işık' in three that must merge separately from it - the dotted and
dotless i are different letters.
"""

ISTANBUL_TEXT = (
    "İstanbul çok büyük bir şehirdir. İstanbul her gün milyonlarca insanı ağırlar. "
    "istanbul sokakları çok kalabalıktır. İSTANBUL boğazı çok güzeldir. "
    "İstanbul her mevsim güzeldir. istanbul kışın çok soğuk olur."
)

ISIK_TEXT = (
    "Işık hızı çok yüksektir. ışık her yerde vardır. IŞIK olmadan görmek zordur. "
    "Işık dalgaları çok küçüktür. ışık kaynağı çok parlaktır. "
    "IŞIK yılı bir uzunluk birimidir. Işık odaya doldu. ışık yavaşça söndü."
)
