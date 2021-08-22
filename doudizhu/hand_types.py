from abc import ABC
from dataclasses import dataclass
from typing import List, Optional, Tuple, Type
from collections import Counter

names = {1: "single", 2: "pair", 3: "triple", 4: "quad"}
discard_moves = {"triple": 1, "quad": 2, "2-triple straight": 2, "3-triple straight": 3}


class HandType(ABC):
    name: str = "Abstract Hand"

    @classmethod
    def classify_hand(cls, hand: List[int]):
        return cls


@dataclass
class InvalidType(HandType):
    name = "InvalidType"

    def __str__(self):
        return self.name


class Empty(HandType):
    name = "empty"


class Rocket(HandType):
    name = "rocket"


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


def validate_hand(hand: List[int]):
    if len(hand) == 0:
        return Empty()
    if sorted(hand) == [16, 17]:
        return Rocket()
    temp = Set.classify_hand(hand)
    if temp is None:
        temp = Run.classify_hand(hand)

    if temp is None:
        return InvalidType()

    return temp


def validate_discard(discard: List[int], hand_type: Type[HandType]):
    if hand_type == InvalidType():
        return InvalidType()
    elif len(discard) == 0:
        return Empty()
    else:
        discard_type = Discard.classify_hand(discard)
        n_discards = discard_moves.get(hand_type.name, 0)
        if discard_type.n_cards == n_discards:
            return discard_type

    return InvalidType()


def validate_move(
    hand: List[int],
    discard: List[int],
    existing_hand_type: Optional[Type[HandType]] = None,
    existing_discard_type: Optional[Type[HandType]] = None,
) -> Tuple[Type[HandType], Type[HandType]]:

    hand_type = validate_hand(hand)
    discard_type = validate_discard(discard, hand_type)
    if hand_type.name == "InvalidMove":
        raise RuntimeError(f"Attempted invalid move: {hand}")
    elif discard_type.name == "InvalidMove":
        raise RuntimeError(f"Attempted invalid discard: {discard_type}")
    elif existing_hand_type is None and existing_discard_type is None:
        if hand_type.name == "Empty":
            raise RuntimeError("Attempted to pass on the first move")
        return hand_type, discard_type
    elif (
        hand_type.name == existing_hand_type.name
        and discard_type.name == existing_discard_type.name
    ):
        if hand_type > existing_hand_type:
            return hand_type, discard_type
        else:
            raise RuntimeError("Attempted move is weaker than last hand")
    else:
        raise (
            f"""Hand type and discard type did not match what was required
                    ({hand_type} !=  {existing_hand_type}
                    or {discard_type} != {existing_discard_type}"""
        )


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
