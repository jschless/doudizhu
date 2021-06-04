from enum import Enum
from collections import Counter


class Rank(Enum):
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14
    TWO = 15
    SMALL_JOKER = 16
    BIG_JOKER = 17

    def __gt__(self, other: "Rank") -> bool:
        return self.value > other.value

    def __lt__(self, other: "Rank") -> bool:
        return self.value < other.value