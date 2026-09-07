"""Corpora for the contrastive scoring tests.

The target is football writing; the control is general English. 'the' is
frequent in both and must not rank; 'offside' and 'referee' are frequent
only in the target and must.
"""

FOOTBALL = " ".join(
    [
        "The referee gave a free kick near the box.",
        "The referee blew for offside again.",
        "A striker was caught offside by the referee.",
        "The referee booked the striker for a late tackle.",
        "Offside decisions frustrate the striker and the crowd.",
        "The crowd booed the referee after the offside call.",
        "A free kick was awarded when the striker was fouled.",
        "The striker scored from the free kick.",
    ]
    * 2
)

GENERAL = " ".join(
    [
        "The weather was warm and the garden looked well.",
        "She read the book in the afternoon and enjoyed it.",
        "The train was late and the platform was crowded.",
        "He wrote the letter and posted it in the morning.",
        "The meeting was long and the room was warm.",
        "They walked to the shop and bought the bread.",
        "The film was good and the music was better.",
        "The dog slept while the cat watched the birds.",
    ]
    * 2
)
