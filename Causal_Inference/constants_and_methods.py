from collections import Counter
import copy


" Constants "

SUITS = ['♦', '♣', '♥', '♠']
DIMOND, HEART, SPADE, CLUB = '♦', '♥',  '♠', '♣'
J, Q, K, A = 11, 12, 13, 14
RANKS = [2, 3, 4, 5, 6, 7, 8, 9, 10, J, Q, K, A]

SUIT_MAPPER = {'d': '♦', 'c': '♣', 'h': '♥', 's': '♠'}

ROYAL_FLUSH = 9
STRAIGHT_FLUSH = 8
FOUR_OF_A_KIND = 7
FULL_HOUSE = 6
FLUSH = 5
STRAIGHT = 4
THREE_OF_A_KIND = 3
TWO_PAIR = 2
ONE_PAIR = 1
HIGH_CARD = 0

STARTING_HANDS_RANKING = [
    'AAo', 'KKo', 'QQo', 'AKs', 'JJo', 'AQs', 'KQs', 'AJs', 'KJs', 'TTo', 'AKo', 'ATs', 'QJs', 'KTs', 'QTs', 'JTs',
    '99o', 'AQo', 'A9s', 'KQo', '88o', 'K9s', 'T9s', 'A8s', 'Q9s', 'J9s', 'AJo', 'A5s', '77o', 'A7s', 'KJo', 'A4s',
    'A3s', 'A6s', 'QJo', '66o', 'K8s', 'T8s', 'A2s', '98s', 'J8s', 'ATo', 'Q8s', 'K7s', 'KTo', '55o', 'JTo', '87s',
    'QTo', '44o', '22o', '33o', 'K6s', '97s', 'K5s', '76s', 'T7s', 'K4s', 'K2s', 'K3s', 'Q7s', '86s', '65s', 'J7s',
    '54s', 'Q6s', '75s', '96s', 'Q5s', '64s', 'Q4s', 'Q3s', 'T9o', 'T6s', 'Q2s', 'A9o', '53s', '85s', 'J6s', 'J9o',
    'K9o', 'J5s', 'Q9o', '43s', '74s', 'J4s', 'J3s', '95s', 'J2s', '63s', 'A8o', '52s', 'T5s', '84s', 'T4s', 'T3s',
    '42s', 'T2s', '98o', 'T8o', 'A5o', 'A7o', '73s', 'A4o', '32s', '94s', '93s', 'J8o', 'A3o', '62s', '92s', 'K8o',
    'A6o', '87o', 'Q8o', '83s', 'A2o', '82s', '97o', '72s', '76o', 'K7o', '65o', 'T7o', 'K6o', '86o', '54o', 'K5o',
    'J7o', '75o', 'Q7o', 'K4o', 'K3o', '96o', 'K2o', '64o', 'Q6o', '53o', '85o', 'T6o', 'Q5o', '43o', 'Q4o', 'Q3o',
    '74o', 'Q2o', 'J6o', '63o', 'J5o', '95o', '52o', 'J4o', 'J3o', '42o', 'J2o', '84o', 'T5o', 'T4o', '32o', 'T3o',
    '73o', 'T2o', '62o', '94o', '93o', '92o', '83o', '82o', '72o']

FLOP_ORDER_HASH = {tup: idx for idx, tup in enumerate((i, j) for i in range(4) for j in range(i, 4))}


" Auxiliary Classes "


class Card:
    """ represent a card in the deck """

    def __init__(self, value: int, suit: str):
        # card attributes
        self.value = value
        self.suit = suit

        mapper = {14: 'A', 13: 'K', 12: 'Q', 11: 'J', 10: 'T'}
        self.str_value = str(value) if value<10 else mapper[value]
        self.suit_mapper = {'♦': 'd', '♣': 'c', '♥': 'h', '♠': 's'}

    def __repr__(self):
        # card_value = str(self.value) if self.value not in self.mapper else self.mapper[self.value]
        # card_value = str(self.value) if self.value not in self.mapper else self.mapper[self.value]
        # card_suit = self.suit
        return self.str_value + self.suit

    def get_card_rep(self):
        # return vector that represent the card
        pass

    def get_card_str_rep(self):
        # return str(self.value) + self.suit_mapper[self.suit]  # changed it for HP model
        return self.str_value + self.suit_mapper[self.suit]

    def __eq__(self, other):
        if isinstance(other, Card):
            return self.value == other.value and self.suit == other.suit
        return False

    def __hash__(self):
        # Combine value and suit into a tuple for hashing
        return hash((self.value, self.suit))


class FinalHand:
    """ represent a final hand strength """
    def __init__(self, seven_cards: list, hand_rank: int, rank_size: int, kickers: list = None):
        self.seven_cards = seven_cards
        self.hand_rank = hand_rank  # flush, two-pair, ...
        self.rank_size = rank_size  # 10 high flush, 4 of a kind of Js
        self.kickers = kickers  # for pair: [10, 5, 2]
        if self.kickers is not None:
            self.kickers.reverse()

    def __repr__(self):
        return f"hand rank = {self.hand_rank}, rank size = {self.rank_size}, kickers = {self.kickers}"


" Auxiliary Methods "


def evaluate_hand(cards_to_check):
    """ return the best hand possible out of this cards """

    def get_suites(arr):
        " return the name of the suits with  at least 5 cards "
        count = {s: 0 for s in SUITS}
        for card in arr:
            count[card.suit] += 1
        for suit_key in count:
            if count[suit_key] >= 5:
                return suit_key
        return None

    def is_increasing(arr):
        """ check for 5 consecutive increasing cards (e.g. 12345)"""
        for i in range(len(arr) - 1):
            if arr[i].value != arr[i + 1].value - 1:
                return False
        return True

    def all_suited(arr):
        """ check if all cards in 'arr' has the same suit"""
        pos_suit = arr[-1].suit
        for inst in arr:
            if inst.suit != pos_suit:
                return False
        return True

    # sort cards
    cards_to_check.sort(key=lambda inst: inst.value)

    # save only cards values
    cards_nums = [card.value for card in cards_to_check]

    # save cards counts
    counts = Counter(cards_nums)

    # ______________________________________________________________________________________________

    """ check for straight & Royal Flush / Straight Flush"""
    # stop and return only if got royal flush /straight flush

    got_straight = False
    royal_flag = False
    straight = {'rank': 0}
    royal_straight = {'rank': 0}

    # create copy of the cards and remove duplicates (cards with same value number)
    cards_copy = copy.deepcopy(cards_to_check)
    flush_pos_suit = get_suites(cards_copy)
    duplicated_indices = []
    for i in range(1, len(cards_copy)):
        if cards_copy[i - 1].value == cards_copy[i].value:
            duplicated_indices.append(i)
    duplicated_indices.reverse()
    for i in duplicated_indices:
        del cards_copy[i]

    # when duplicate were removed, keep the duplicate with a suit that can create royal/straight flush
    if len(cards_copy) >= 5 and flush_pos_suit:
        for i in range(5):
            cur_card = cards_copy[i]
            new_card = Card(cur_card.value, flush_pos_suit)
            if new_card in cards_to_check:
                cards_copy[i] = new_card

    # add A to the begging to represent 1 if needed
    if cards_to_check[-1].value == A:
        # cards_copy.insert(0, copy.copy(cards_to_check[-1]))
        cards_copy.insert(0, Card(1, cards_to_check[-1].suit))

    # check for straight
    for i in range(len(cards_copy) - 4):
        if is_increasing(cards_copy[i:i + 5]):
            got_straight = True
            straight['rank'] = max(straight['rank'], cards_copy[i + 4].value)

            # check for flush + straight
            if all_suited(cards_copy[i:i + 5]):
                royal_flag = True
                royal_straight['rank'] = max(royal_straight['rank'], cards_copy[i + 4].value)

    if royal_flag is True:
        return FinalHand(seven_cards=cards_to_check, hand_rank=ROYAL_FLUSH,
                         rank_size=royal_straight['rank'])

    """ _____ check for 4 of a kind _____ """

    got_4_of_kind = False
    four_of_kind = {}

    if len(counts.keys()) < 5:  # 4 of a kind is possible
        for card_num in counts.keys():
            if counts[card_num] == 4:
                got_4_of_kind = True
                four_of_kind['rank'] = card_num
                break  # can't be another option

        # find rank and kicker
        if got_4_of_kind is True:
            four_of_kind['kicker'] = 0
            for card_num in counts.keys():
                if card_num != four_of_kind['rank']:
                    four_of_kind['kicker'] = max(four_of_kind['kicker'], card_num)

    if got_4_of_kind is True:
        return FinalHand(seven_cards=cards_to_check, hand_rank=FOUR_OF_A_KIND,
                         rank_size=four_of_kind['rank'], kickers=[four_of_kind['kicker']])

    """ _____ check for FULL HOUSE & 3 OF A KIND & 2 PAIRS & 1 PAIR _____ """

    got_full_house = False
    full_house = {}

    got_3_of_kind = False
    three_of_kind = {}

    got_2_pairs = False
    two_pairs = {}

    got_1_pair = False
    one_pair = {}

    same_3, same_2 = [], []
    for card_num in counts.keys():
        if counts[card_num] == 3:
            same_3.append(card_num)
        elif counts[card_num] == 2:
            same_2.append(card_num)

    # full house
    if len(same_3) == 2:
        got_full_house = True
        full_house['3'] = max(same_3)
        full_house['2'] = min(same_3)
    elif len(same_3) == 1 and len(same_2) >= 1:
        got_full_house = True
        full_house['3'] = max(same_3)
        full_house['2'] = max(same_2)

    if got_full_house:
        full_house_rank = 13 * full_house['3'] + full_house['2']
        return FinalHand(seven_cards=cards_to_check, hand_rank=FULL_HOUSE,
                         rank_size=full_house_rank)

    # 3 of a kind
    if len(same_3) == 1:
        got_3_of_kind = True
        three_of_kind['rank'] = same_3[0]
        # find kickers
        pos_cards = sorted([c.value for c in cards_to_check if c.value != three_of_kind['rank']])
        three_of_kind['kicker'] = pos_cards[-2:]

    # two pairs
    if len(same_2) > 1:
        got_2_pairs = True
        two_pairs['rank'] = sorted(same_2)[-2:]
        # find kickers
        pos_cards = sorted([c.value for c in cards_to_check if c.value not in two_pairs['rank']])
        two_pairs['kicker'] = pos_cards[-1]

    # one pair
    if len(same_2) == 1:
        got_1_pair = True
        one_pair['rank'] = same_2[0]
        # find kickers
        pos_cards = sorted([c.value for c in cards_to_check if c.value != one_pair['rank']])
        one_pair['kicker'] = pos_cards[-3:]

    " _____________________ check for FLUSH _____________________ "

    # check for flush po (5 suited cards)
    suit_5plus = get_suites(cards_to_check)

    got_flush = False
    flush = {}
    kickers = []

    if suit_5plus is not None:
        got_flush = True
        flush['rank'] = 0
        for card in cards_to_check:
            if card.suit == suit_5plus:
                flush['rank'] = max(flush['rank'], card.value)
                kickers.append(card.value)

    if got_flush:
        return FinalHand(seven_cards=cards_to_check, hand_rank=FLUSH,
                         rank_size=flush['rank'], kickers=sorted(kickers))

    if got_straight:
        return FinalHand(seven_cards=cards_to_check, hand_rank=STRAIGHT,
                         rank_size=straight['rank'])

    # _____________________ check for 3 OF A KIND / 2 PAIRS / 1 PAIR _____________________ "

    if got_3_of_kind:
        return FinalHand(seven_cards=cards_to_check, hand_rank=THREE_OF_A_KIND,
                         rank_size=three_of_kind['rank'], kickers=three_of_kind['kicker'])

    if got_2_pairs:
        two_pairs_rank = 169 * two_pairs['rank'][1] + 13 * two_pairs['rank'][0]
        return FinalHand(seven_cards=cards_to_check, hand_rank=TWO_PAIR,
                         rank_size=two_pairs_rank, kickers=[two_pairs['kicker']])

    if got_1_pair:
        return FinalHand(seven_cards=cards_to_check, hand_rank=ONE_PAIR,
                         rank_size=one_pair['rank'], kickers=one_pair['kicker'])

    return FinalHand(seven_cards=cards_to_check, hand_rank=HIGH_CARD,
                     rank_size=max(list(counts.keys())), kickers=sorted(list(counts.keys()))[-5:])


def expand_evaluate_hand(cards_to_check):
    """ return possible draws with given cards """

    suits = [c.suit for c in cards_to_check]
    values = [c.value for c in cards_to_check]

    flush_draw = False
    runner_flush_draw = False
    straight_draw = False
    runner_straight_draw = False

    suit_count = Counter(suits)
    suit_count_values = list(suit_count.values())
    if 4 in suit_count_values:
        flush_draw = True
    elif 3 in suit_count_values:
        runner_flush_draw = True

    values = sorted(set(values))
    if 14 in values:
        values.insert(0, 1)
    count = 1
    for i in range(len(values) - 1):
        if values[i] == values[i + 1] - 1:
            count += 1
            if count == 4:
                straight_draw = True
            elif count == 3:
                runner_straight_draw = True
        else:
            count = 1
    if len(cards_to_check) == 5:
        return flush_draw, runner_flush_draw, straight_draw, runner_straight_draw
    else:
        return runner_flush_draw, runner_straight_draw


def get_hand_equivalence_class(hand, type_='Card'):
    """ map each hand (two cards) into suit/ of suit representation """

    card_1, card_2 = hand
    if type_ == 'str':
        mapper = {'A': 14, 'K': 13, 'Q': 12, 'J': 11, 'T': 10}
        c1_value, c2_value = card_1[0], card_2[0]
        if card_1[0] in ['A', 'K', 'Q', 'J', 'T']:
            c1_value = mapper[card_1[0]]
        else:
            c1_value = int(c1_value)

        if card_2[0] in ['A', 'K', 'Q', 'J', 'T']:
            c2_value = mapper[card_2[0]]
        else:
            c2_value = int(c2_value)

        if c1_value >= c2_value:
            values = [card_1[0], card_2[0]]
        else:
            values = [card_2[0], card_1[0]]

        eq = values[0] + values[1]

        if card_1[1] == card_2[1]:
            eq += 's'
        else:
            eq += 'o'

    elif type_ == 'Card':

        if card_1.value >= card_2.value:
            values = [card_1.str_value, card_2.str_value]
        else:
            values = [card_2.str_value, card_1.str_value]

        eq = str(values[0]) + str(values[1])

        if card_1.suit == card_2.suit:  # is suited
            eq += 's'
        else:
            eq += 'o'

    else:
        raise RuntimeError("unknown type_")

    return eq


def get_hand_rep(hand):
    """ get hash value correspond to the given hand """
    # hash over possible starting hands (total 196)
    hand_rep = get_hand_equivalence_class(hand, type_='Card')
    hand_hash_val = STARTING_HANDS_RANKING.index(hand_rep)
    return hand_hash_val


def get_order_score(flop_cards, hero_cards):
    """
    assume (At leasts for now) each card is instance of Card
    """
    board_values = [c.value for c in flop_cards]
    order_value = []
    for c in hero_cards:
        order_value.append(sum([c.value > bv for bv in board_values]))
    return FLOP_ORDER_HASH[tuple(sorted(order_value))]



