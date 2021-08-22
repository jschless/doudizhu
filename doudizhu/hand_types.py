from abc import ABC
from dataclasses import dataclass
from typing import List, Type
from collections import Counter

names = {1: "single", 2: "pair", 3: "triple", 4: "quad"}
discard_moves = {"triple": 1, "quad": 2, "2-triple straight": 2, "3-triple straight": 3}


def validate_hand(hand: List[int]):
    temp = Set.classify_hand(hand)
    if temp is None:
        temp = Run.classify_hand(hand)

    if temp is None:
        return InvalidType()

    return temp


class HandType(ABC):
    name: str = "Abstract Hand"

    @classmethod
    def classify_hand(cls, hand: List[int]):
        return cls


def validate_discard(discard: List[int], hand_type: Type[HandType]):
    if len(discard) == 0:
        return Empty()
    else:
        discard_type = Discard.classify_hand(discard)
        n_discards = discard_moves.get(hand_type.name, 0)
        if discard_type.n_cards == n_discards:
            return discard_type

    return InvalidType


class InvalidType(HandType):
    name = "InvalidType"

    def __str__(self):
        return self.name


class Empty(HandType):
    name = "Empty"


@dataclass(order=True)
class Discard(HandType):
    n_cards: int
    freq: int

    @classmethod
    def classify_hand(cls, hand: List[int]):
        counter = Counter(sorted(hand))
        values, counts = list(counter.keys()), list(counter.values())
        if len(set(counts)) == 1:
            return cls(n_cards=len(values), freq=counts[0])
        else:
            return InvalidType()

    @property
    def name(self):
        return f"{self.n_cards}-{names[self.freq]}"

    def __str__(self):
        return self.name


@dataclass(order=True)
class Set(HandType):
    value: int
    freq: int

    @classmethod
    def classify_hand(cls, hand: List[int]):
        counter = Counter(sorted(hand))
        values, counts = list(counter.keys()), list(counter.values())
        if len(values) > 1:
            return None  # more than one value
        return cls(value=values[0], freq=counts[0])

    @property
    def name(self):
        return names[self.freq]

    def __str__(self):
        return f"{self.freq}-{self.name}"


@dataclass(order=True)
class Run(HandType):
    start: int
    freq: int
    n_cards: int

    @classmethod
    def classify_hand(cls, hand: List[int]):
        counter = Counter(sorted(hand))
        values, counts = list(counter.keys()), list(counter.values())

        for i in [15, 16, 17]:
            if i in values:
                return None  # run includes two or jokers

        last_val = values[0]
        # check if it is a run
        for i in values[1:]:
            if i - last_val != 1:
                return None  # this is not a run
            last_val = i

        freq = counts[0]
        n_cards = len(values)

        if (
            freq == 2
            and n_cards < 3
            or freq == 3
            and n_cards < 2
            or freq == 1
            and n_cards < 5
        ):
            return None  # not enough cards in a row

        if len(set(counts)) > 1:
            return None  # frequencies differ

        return cls(start=values[0], n_cards=n_cards, freq=freq)

    def build_options_from_deck(self, deck: List[int]) -> List[List[int]]:
        """Takes a deck of cards and returns all possible hand types

        Args:
            deck (List[int]): list of ints representing card deck

        Returns:
            List[List[int]]: list of possible hands that match this type
        """
        pass

    @property
    def name(self):
        return f"{self.n_cards}-{names[self.freq]} straight"

    def __str__(self):
        return f"{self.name} from {self.start}"


# print(Set.classify_hand([3, 3, 3, 3]))
# print(Set.classify_hand([3, 3, 3, 3, 4]))

# print(Run.classify_hand([4, 5, 6, 7, 8, 9]))
# print(Run.classify_hand([4, 4, 5, 5]))
# print(Run.classify_hand([4, 4, 4, 5, 5, 5]))
# a = Run.classify_hand([4, 4, 5, 5, 6, 6])
# b = Run.classify_hand([7, 7, 5, 5, 6, 6])
# print(b > a)
# print(b.name == a.name)

# print(Discard.classify_hand([3, 3, 4, 4]))
# print(Discard.classify_hand([3, 3, 4, 4, 5]))
# print(Discard.classify_hand([3, 3, 4, 4, 4]))
# print(Discard.classify_hand([3, 4]))