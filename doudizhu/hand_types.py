from abc import ABC
from dataclasses import dataclass
from typing import List, Tuple, Type
from collections import Counter

names = {1: "single", 2: "pair", 3: "triple", 4: "quad"}
discard_moves = {"triple": 1, "quad": 2, "2-triple straight": 2, "3-triple straight": 3}


class HandType(ABC):
    name: str = "Abstract Hand"

    @classmethod
    def classify_hand(cls, hand: List[int]):
        return cls


@dataclass
class UninitializedType(HandType):
    name: str = "UninitializedType"


@dataclass
class InvalidType(HandType):
    name: str = "InvalidType"

    def __str__(self):
        return self.name


@dataclass
class Empty(HandType):
    name: str = "Empty"

    def __str__(self):
        return "no attachments"


@dataclass
class Rocket(HandType):
    name: str = "Rocket"

    def __str__(self):
        return "rocket"

    def can_move(self, cards: List[int]) -> bool:
        """Returns whether a player can move with given hands

        Args:
            cards (List[int]): Available cards to make a move

        Returns:
            bool: Whether a move can be made with the inputted cards
        """
        return False


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

    def can_move(self, cards: List[int]) -> bool:
        """Returns whether a player can move with given hands

        Args:
            cards (List[int]): Available cards to make a move

        Returns:
            bool: Whether a move can be made with the inputted cards
        """
        for value, count in Counter(sorted(cards)).items():
            if value > self.value and count == self.freq:
                return True
        return False

    @property
    def name(self):
        return names[self.freq]

    def __str__(self):
        return f"{self.value}-{self.name}"


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

    def can_move(self, cards: List[int]) -> bool:
        """Returns whether a player can move with given hands

        Args:
            cards (List[int]): Available cards to make a move

        Returns:
            bool: Whether a move can be made with the inputted cards
        """
        # remove impossible values
        forbidden = [15, 16, 17]
        cards = [c for c in cards if c > self.start and c not in forbidden]
        attempt = []
        for card, freq in sorted(Counter(cards).items()):
            if len(attempt) == 0:
                # if we have no attempt and can start one, do so
                if freq == self.freq:
                    attempt.append(card)
            elif (card - attempt[-1] == 1) and freq == self.freq:
                # build if it's the right freq and it's next in sequence
                attempt.append(card)
            else:
                attempt = []

            if len(attempt) == self.n_cards:
                return True

        return False

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
    existing_hand_type: Type[HandType],
    existing_discard_type: Type[HandType],
) -> Tuple[Type[HandType], Type[HandType]]:

    hand_type = validate_hand(hand)
    discard_type = validate_discard(discard, hand_type)
    print(hand_type, discard_type)
    if hand_type == InvalidType():
        raise RuntimeError(f"Attempted invalid move: {hand}")
    elif discard_type == InvalidType():
        raise RuntimeError(f"Attempted invalid discard: {discard_type}")
    elif (
        existing_hand_type == UninitializedType()
        and existing_discard_type == UninitializedType()
    ):
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
    elif hand_type == Empty() and discard_type == Empty():
        return hand_type, discard_type
    elif (
        hand_type.name == "quad" and discard_type == Empty()
    ) or hand_type == Rocket():
        return hand_type, discard_type
    else:
        raise RuntimeError(
            f"""Hand type and discard type did not match what was required
                    ({hand_type} !=  {existing_hand_type}
                    or {discard_type} != {existing_discard_type}"""
        )


def hand_type_from_dict(args: dict) -> HandType:
    name = args.get("name", "")
    if name == "Empty":
        return Empty()
    elif name == "InvalidType":
        return InvalidType()
    elif name == "UninitializedType":
        return UninitializedType()
    elif name == "Rocket":
        return Rocket()
    elif "start" in args:
        return Run(**args)
    elif "n_cards" in args:
        return Discard(**args)
    else:
        return Set(**args)
