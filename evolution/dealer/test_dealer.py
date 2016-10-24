import json

from collections import OrderedDict
from functools import partial

from unittest import TestCase
from unittest.mock import MagicMock, call

from .dealer import Dealer, TraitCard
from ..data_definitions import DataDefinitions
from ..player.player import Player
from ..player.dummy_player import DummyPlayer
from ..common.species import Species
from ..common.trait import Trait, HORNS_DAMAGE
from ..common.actions import Actions, GrowPopulation, GrowBody, BoardTransfer, ReplaceTrait


class DealerTestCase(TestCase):

    def setUp(self):

        self.tc1 = TraitCard(1, Trait.LONG_NECK)
        self.tc2 = TraitCard(-8, Trait.CARNIVORE)
        self.tc3 = TraitCard(-3, Trait.SCAVENGER)

        self.p1 = Player(1, external=DummyPlayer())
        self.p2 = Player(2, cards=[self.tc3], external=DummyPlayer())
        self.p3 = Player(3, external=DummyPlayer())

    def test_serialize_deserialize(self):

        configs = [
            [[self.p1.serialize(), self.p2.serialize(), self.p3.serialize()],
             10,
             [self.tc1.serialize(), self.tc2.serialize()]]
        ]

        for config in configs:
            deserialized = Dealer.deserialize(config)
            self.assertEqual(deserialized.serialize(), config)

    def test_ranking(self):
        players = [
            Player(1, bag=10),
            Player(2, bag=1),
            Player(3, bag=5)
        ]
        dealer = Dealer(players, 0, [])
        self.assertEqual(dealer.players, players)
        self.assertEqual([r for r in dealer.ranking()], [(1, 10), (3, 5), (2, 1)])
        self.assertEqual(dealer.players, players)

    def test_get_current_player(self):
        player_list = [self.p1, self.p2]
        d = Dealer(players=player_list, watering_hole=10, deck=[self.tc1, self.tc2])
        self.assertEqual(d.get_current_player(), player_list[0])

    def test_player_queue_all(self):
        player_list = [self.p1, self.p2, self.p3]
        d = Dealer(players=player_list, watering_hole=10, deck=[self.tc1, self.tc2])
        self.assertEqual(d.player_queue_all, player_list)
        # move onto the next player
        d.rotate_active_players()
        rotated_player_list = [self.p2, self.p3, self.p1]
        self.assertEqual(d.player_queue_all, rotated_player_list)
        # even if we remove p2 as active it should stay in the queue, but active is now p3
        d.active_players.remove(self.p2)
        rotated_player_list_1 = [self.p3, self.p1, self.p2]
        self.assertEqual(d.player_queue_all, rotated_player_list_1)

    def test_scavenge(self):
        """ When food is taken all players should be notified and act accordingly """
        watering_hole = 10
        player_list = [MagicMock(), MagicMock(), MagicMock()]
        # everyone takes one food
        for player in player_list:
            player.scavenge.return_value = 1

        d = Dealer(players=player_list, watering_hole=watering_hole, deck=[])
        self.assertEqual(d.watering_hole, watering_hole)
        self.assertEqual(d.player_queue_all, player_list)

        for player in d.player_queue_all:
            self.assertFalse(player.scavenge.called)

        d.scavenge()

        for idx, player in enumerate(d.player_queue_all):
            food_taken_so_far = idx
            player.scavenge.assert_called_once_with(watering_hole - food_taken_so_far)

        self.assertEqual(d.watering_hole, watering_hole - len(player_list))

    def test_feed_species(self):
        watering_hole = 10

        player = MagicMock()
        player.feed_species.return_value = 1

        species = Species()

        d = Dealer(players=[player], watering_hole=10, deck=[])
        self.assertEqual(d.watering_hole, watering_hole)

        d.feed_species(player, species)
        player.feed_species.assert_called_once_with(species, watering_hole)

        self.assertEqual(d.watering_hole, watering_hole - player.feed_species.return_value)

    def test_feed_species_fat_tissue(self):
        watering_hole = 10
        stored_food_tokens = 1

        player = MagicMock()
        species = Species()

        d = Dealer(players=[player], watering_hole=10, deck=[])
        self.assertEqual(d.watering_hole, watering_hole)

        d.feed_species_fat_tissue(player, species, stored_food_tokens)
        player.store_fat_tissue.assert_called_once_with(species, stored_food_tokens)

        self.assertEqual(d.watering_hole, watering_hole - stored_food_tokens)

    def test_deal_cards(self):

        deck = [self.tc1, self.tc2, self.tc3]

        d = Dealer(players=[], watering_hole=0, deck=deck)
        self.assertEqual(d.deck, deck)

        to_deal = 1
        dealt = d.deal_cards(to_deal)
        self.assertEqual(len(dealt), to_deal)
        self.assertEqual(dealt, deck[:to_deal])
        remaining_deck = deck[to_deal:]
        self.assertEqual(d.deck, remaining_deck)

        # deal more than available
        to_deal = 3
        available = len(d.deck)
        self.assertGreater(to_deal, available)

        dealt = d.deal_cards(to_deal)
        self.assertEqual(len(dealt), available)
        self.assertEqual(dealt, remaining_deck)
        self.assertEqual(d.deck, [])

    def test_species_extinct(self):

        deck = [self.tc1, self.tc2, self.tc3]

        p = Player(idx=19)
        d = Dealer(players=[p], watering_hole=0, deck=deck)
        self.assertEqual(d.deck, deck)
        self.assertEqual(p.cards, [])

        d.species_extinct(p)

        self.assertGreater(d.EXTINCT_SPECIES_PAYOUT, 0)
        self.assertEqual(d.deck, deck[d.EXTINCT_SPECIES_PAYOUT:])
        self.assertEqual(p.cards, deck[:d.EXTINCT_SPECIES_PAYOUT])

    def test_carnivore_feeding_no_horns_attacker_lives(self):

        p1 = MagicMock()
        p2 = MagicMock()
        p3 = MagicMock()

        players = [p1, p2, p3]

        def carnivore_feeding_tester(players, species_idx, player_idx, defender_idx):
            current_player = players[0]
            target_list = players[1:] + players[:1]

            d = Dealer(players=players, watering_hole=10, deck=[])
            # defender doesn't have horns and doesn't go extinct
            d.hurt_species = MagicMock(return_value=(False, False))
            d.feed_species = MagicMock()
            d.scavenge = MagicMock()

            d.carnivore_feeding(species_idx, player_idx, defender_idx)
            d.hurt_species.assert_called_once_with(target_list[player_idx], defender_idx,
                                                   d.CARNIVORE_ATTACK_POPULATION_DECREASE)
            d.feed_species.assert_called_once_with(current_player, species_idx)
            d.scavenge.assert_called_once_with()

        # attacks p2
        carnivore_feeding_tester(players, 0, 0, 0)
        # attacks p3
        carnivore_feeding_tester(players, 0, 1, 0)
        # attacks itself
        carnivore_feeding_tester(players, 0, 2, 0)

    def test_carnivore_feeding_horns_attacker_lives(self):

        p1 = MagicMock()
        p2 = MagicMock()
        p3 = MagicMock()

        players = [p1, p2, p3]

        def carnivore_feeding_tester(players, attacker_idx, player_idx, defender_idx):
            current_player = players[0]
            target_list = players[1:] + players[:1]

            d = Dealer(players=players, watering_hole=10, deck=[])
            # defender has horns and doesn't go extinct, attacker doesn't go extinct
            d.hurt_species = MagicMock(side_effect=[(False, True), (False, False)])
            d.feed_species = MagicMock()
            d.scavenge = MagicMock()

            expected_hurt_calls = [
                call(target_list[player_idx], defender_idx, d.CARNIVORE_ATTACK_POPULATION_DECREASE),
                call(current_player, attacker_idx, HORNS_DAMAGE)
            ]

            d.carnivore_feeding(attacker_idx, player_idx, defender_idx)
            self.assertEqual(d.hurt_species.call_args_list, expected_hurt_calls)
            d.feed_species.assert_called_once_with(current_player, attacker_idx)
            d.scavenge.assert_called_once_with()

        # attacks p2
        carnivore_feeding_tester(players, 0, 0, 0)
        # attacks p3
        carnivore_feeding_tester(players, 0, 1, 0)
        # attacks itself
        carnivore_feeding_tester(players, 0, 2, 0)

    def test_carnivore_feeding_horns_attacker_dies(self):

        p1 = MagicMock()
        p2 = MagicMock()
        p3 = MagicMock()

        players = [p1, p2, p3]

        def carnivore_feeding_tester(oplayers, attacker_idx, player_idx, defender_idx):
            players = oplayers.copy()
            current_player = players[0]
            target_list = players[1:] + players[:1]

            d = Dealer(players=players, watering_hole=10, deck=[])
            # defender has horns and doesn't go extinct, attacker goes extinct
            d.hurt_species = MagicMock(side_effect=[(False, True), (True, False)])
            d.feed_species = MagicMock()
            d.scavenge = MagicMock()

            expected_hurt_calls = [
                call(target_list[player_idx], defender_idx, d.CARNIVORE_ATTACK_POPULATION_DECREASE),
                call(current_player, attacker_idx, HORNS_DAMAGE)
            ]

            d.carnivore_feeding(attacker_idx, player_idx, defender_idx)
            self.assertEqual(d.hurt_species.call_args_list, expected_hurt_calls)
            self.assertFalse(d.feed_species.called)
            self.assertFalse(d.scavenge.called)

        # attacks p2
        carnivore_feeding_tester(players, 0, 0, 0)
        # attacks p3
        carnivore_feeding_tester(players, 0, 1, 0)
        # attacks itself
        carnivore_feeding_tester(players, 0, 2, 0)

    def test_auto_traits(self):
        p1 = MagicMock()
        p2 = MagicMock()
        p3 = MagicMock()

        p1.auto_traits.return_value = 1
        p2.auto_traits.return_value = 3
        p3.auto_traits.return_value = 4

        watering_hole = 10
        d = Dealer(players=[p1, p2, p3], watering_hole=watering_hole, deck=[])
        d.auto_traits()
        p1.auto_traits.assert_called_with(watering_hole)
        p2.auto_traits.assert_called_with(watering_hole - p1.auto_traits.return_value)
        p3.auto_traits.assert_called_with(watering_hole - p1.auto_traits.return_value - p2.auto_traits.return_value)
        self.assertEqual(d.watering_hole, (watering_hole - p1.auto_traits.return_value -
                                           p2.auto_traits.return_value - p3.auto_traits.return_value))

    def test_display(self):

        player_list = [self.p1, self.p2, self.p3]
        d = Dealer(players=player_list, watering_hole=10, deck=[self.tc1, self.tc2])

        expected = {
            Dealer.DISPLAY_KEY_WATERING_HOLE: 10,
            Dealer.DISPLAY_KEY_PLAYERS: [p.display() for p in d.players],
            Dealer.DISPLAY_KEY_DECK: [tc.display() for tc in d.deck]
        }
        self.assertEqual(d.display(), expected)

    def test_add_external_players(self):

        d = Dealer(deck=[self.tc1, self.tc2])

        ext_p_1 = DummyPlayer(1)
        ext_p_2 = DummyPlayer(1)
        ext_p_3 = DummyPlayer(1)

        lst = d.add_external_players([ext_p_1, ext_p_2, ext_p_3])

        self.assertEqual(len(d.players), 3)
        self.assertEqual(d.players[0].idx, 1)
        self.assertEqual(d.players[1].idx, 2)
        self.assertEqual(d.players[2].idx, 3)
        self.assertEqual(lst, [1, 2, 3])

    def test_run_game(self):

        p1 = Player(idx=1)
        p2 = Player(idx=2)
        p3 = Player(idx=3)
        p4 = Player(idx=4)
        p5 = Player(idx=5)
        p6 = Player(idx=6)
        p7 = Player(idx=7)
        p8 = Player(idx=8)

        wh = 4
        d = Dealer(watering_hole=wh, players=[p1, p2, p3, p4, p5, p6, p7, p8], deck=[])
        d.run_game()
        for p in d.players:
            self.assertEqual(p.score(), 1)

    def test_run_game_malicious_feeding_choice(self):

        bad_external = DummyPlayer()
        bad_external.feed_next = MagicMock(side_effect=ValueError())

        p1 = Player(idx=1, external=bad_external)
        p2 = Player(idx=2, species=[Species(), Species()], external=bad_external)
        p3 = Player(idx=3, species=[Species()], external=bad_external)

        wh = 4
        d = Dealer(watering_hole=wh, players=[p1, p2, p3])
        d.run_game()
        self.assertEqual(len(d.players), 0)

    def test_run_game_malicious(self):

        bad_external = MagicMock()
        bad_external.choose = MagicMock(side_effect=ValueError())

        p1 = Player(idx=1, external=bad_external)
        p2 = Player(idx=2, external=bad_external)
        p3 = Player(idx=3, external=bad_external)
        p4 = Player(idx=4, external=bad_external)
        p5 = Player(idx=5, external=bad_external)
        p6 = Player(idx=6, external=bad_external)
        p7 = Player(idx=7, external=bad_external)
        p8 = Player(idx=8, external=bad_external)

        wh = 4
        d = Dealer(watering_hole=wh, players=[p1, p2, p3, p4, p5, p6, p7, p8], deck=[])
        d.run_game()
        self.assertEqual(len(d.players), 0)

    def test_num_cards_to_deal(self):

        d = Dealer(deck=[self.tc1, self.tc2])
        ex_player_1 = Player(idx=1)
        ex_player_2 = Player(idx=2, species=[Species(), Species()])

        self.assertEqual(d.num_cards_to_deal(ex_player_1), 4)
        self.assertEqual(d.num_cards_to_deal(ex_player_2), 5)

    def test_step1(self):
        p1 = Player(idx=1)
        p2 = Player(idx=2, species=[Species()])
        p3 = Player(idx=3, species=[Species(), Species(), Species()])

        deck = DataDefinitions.deck()
        wh = 4
        d = Dealer(watering_hole=wh, players=[p1, p2, p3], deck=deck)

        p1.start = MagicMock()
        p2.start = MagicMock()
        p3.start = MagicMock()
        d.step1()
        p1.start.assert_called_once_with(wh, True, deck[0:4])
        p2.start.assert_called_once_with(wh, False, deck[4:8])
        p3.start.assert_called_once_with(wh, False, deck[8:14])
        self.assertEqual(d.players, [p1, p2, p3])

    def test_step1_malicious(self):

        bad_external = MagicMock()
        bad_external.start = MagicMock(side_effect=ValueError())
        p1 = Player(idx=1, external=bad_external)
        p2 = Player(idx=2, species=[Species()], external=DummyPlayer())
        p3 = Player(idx=3, species=[Species(), Species(), Species()], external=DummyPlayer())

        deck = DataDefinitions.deck()
        wh = 4
        d = Dealer(watering_hole=wh, players=[p1, p2, p3], deck=deck)

        d.step1()
        self.assertEqual(d.players, [p2, p3])


class Feed1TestCase(TestCase):

    @staticmethod
    def p(name, *species, cards=None):
        species = list(species)
        cards = cards if cards is not None else []
        return name, species, cards

    def assert_feed1(self, doc, before, deck, pre, post, after):
        """
        :param doc: test case explanation
        :param before: list of lists of species belonging to each player
        :type before: (str, LOS, LOC)
        :param deck: list cards the dealer has
        :param pre: watering hole before the feeding
        :param post: watering hole after the feeding
        :param after: list of lists of species after the feeding
        :type after: (str, LOS, LOC)
        """
        player_registry = {}

        players = []
        for idx, (name, species, cards) in enumerate(before):
            assert name not in player_registry, "players must have unique names"
            player = Player(idx, species=species, cards=cards, external=DummyPlayer())
            players.append(player)
            player_registry[name] = player

        dealer = Dealer(players=players, watering_hole=pre, deck=deck)

        self.assertEqual(dealer.watering_hole, pre)
        self.assertEqual(dealer.deck, deck)

        dealer.feed1()

        cards_dealt = 0
        for name, species, cards in after:
            player = player_registry.pop(name)
            assert len(player.species) == len(species), "player has a different amount of species than expected"
            for actual, expected in zip(player.species, species):
                self.assertEqual(actual, expected, doc)
            if cards:
                self.assertEqual(player.cards, cards)
                cards_dealt += len(cards)

        self.assertEqual(len(player_registry), 0, "all player in before must be in after")
        self.assertEqual(dealer.watering_hole, post)
        self.assertEqual(len(dealer.deck), len(deck) - cards_dealt)

    def test_feed1(self):

        p = self.p

        def s_carnivore(food=0, body=1, population=1):
            return Species(food=food, body=body, population=population, traits=[Trait.CARNIVORE])

        def s_satisfied(p=1, b=None):
            return Species(food=p, population=p, body=b)

        self.assert_feed1(
            doc="population is reduced below food#",
            before=[
              p("attacker", s_carnivore(), s_satisfied()),
              p("attackee", s_satisfied(2)),
              p("by-stand", ),
            ],
            deck=[],
            pre=1,
            post=0,
            after=[
              p("attacker", s_carnivore(food=1), s_satisfied()),
              p("attackee", s_satisfied(1)),
              p("by-stand", ),
            ]
        )

        all_cards = DataDefinitions.deck()
        cards1 = all_cards[:2]
        cards2 = all_cards[2:4]
        cards = cards1 + cards2

        def s_horned():
            return Species(population=1, traits=[Trait.HORNS])

        def s_climbing():
            return Species(traits=[Trait.CLIMBING])

        def s_climbing_satisfied():
            return Species(food=1, traits=[Trait.CLIMBING])

        def s_herbivore(food=0, body=1, population=1):
            return Species(food=food, body=body, population=population)

        def s_fat_tissue(food=0, body=1, population=1, fat_food=0):
            return Species(food=food, body=body, population=population, fat_food=fat_food, traits=[Trait.FAT_TISSUE])

        def s_fat_tissue_full(food=0, body=1):
            return s_fat_tissue(food=food, body=body, fat_food=body)

        def s_with(f=0, p=1, traits=None):
            traits = traits or []
            return Species(food=f, population=p, traits=traits)

        self.assert_feed1(
            doc="attacker attacks attackee and dies from horns",
            before=[
              p("attacker", s_carnivore(), s_satisfied()),
              p("attackee", s_horned()),
            ],
            deck=cards,
            pre=1,
            post=1,
            after=[
              p("attacker", s_satisfied(), cards=cards2),
              p("attackee", cards=cards1),
            ]
        )

        self.assert_feed1(
            doc="hungry carnivore cannot attack, choose vegetarian for player",
            before=[
              p("eater", s_carnivore(), s_climbing()),
              p("protected", s_climbing()),
            ],
            deck=[],
            pre=1,
            post=0,
            after=[
              p("eater", s_carnivore(), s_climbing_satisfied()),
              p("protected", s_climbing()),
            ]
        )

        self.assert_feed1(
            doc="fat tissue species is fed first",
            before=[
              p("eater", s_carnivore(), s_herbivore(), s_fat_tissue()),
              p("other", s_climbing()),
            ],
            deck=[],
            pre=1,
            post=0,
            after=[
              p("eater", s_carnivore(), s_herbivore(), s_fat_tissue(fat_food=1)),
              p("other", s_climbing()),
            ]
        )

        self.assert_feed1(
            doc="fat tissue species cannot store more fat, feed leftmost herbivore",
            before=[
              p("eater", s_carnivore(), s_herbivore(), s_fat_tissue_full()),
              p("other", s_climbing()),
            ],
            deck=[],
            pre=1,
            post=0,
            after=[
              p("eater", s_carnivore(), s_satisfied(b=1), s_fat_tissue_full()),
              p("other", s_climbing()),
            ]
        )

        self.assert_feed1(
            doc="all herbivores satisified, carnivore can attack",
            before=[
              p("eater", s_carnivore(), s_satisfied()),
              p("other", s_herbivore()),
            ],
            deck=[],
            pre=1,
            post=0,
            after=[
              p("eater", s_carnivore(food=1), s_satisfied()),
              p("other"),
            ]
        )

        self.assert_feed1(
            doc="foraging fails, cooperation should fail",
            before=[
              p("p1", s_with(1, 2, [Trait.COOPERATION, Trait.FORAGING]), s_with(0, 2)),
              p("p2", s_satisfied()),
              p("p3", s_satisfied()),
            ],
            deck=[],
            pre=3,
            post=1,
            after=[
              p("p1", s_with(2, 2, [Trait.COOPERATION, Trait.FORAGING]), s_with(1, 2)),
              p("p2", s_satisfied()),
              p("p3", s_satisfied()),
            ]
        )


class Step4TestCase(TestCase):

    @staticmethod
    def c(v, t):
        return TraitCard(v, Trait(t))

    def assertDealerEqual(self, one, two):
        self.assertEqual(one.watering_hole, two.watering_hole)
        self.assertEqual(one.deck, two.deck)

        self.assertEqual(len(one.players), len(two.players))
        for p1, p2 in zip(one.players, two.players):
            self.assertPlayerEqual(p1, p2)

    def assertPlayerEqual(self, one, two):
        self.assertEqual(one.idx, two.idx)
        self.assertEqual(one.species, two.species)
        self.assertEqual(one.bag, two.bag)
        self.assertEqual(one.cards, two.cards)

    @staticmethod
    def generate_dealers(configuration, expected_configuration):
        # create dealer
        players, wh, deck = configuration
        player_registry = OrderedDict((name, player.serialize()) for name, player in players)

        dealer = Dealer.deserialize([player_registry.values(), wh, deck])

        # create expected dealer
        players, wh, deck = expected_configuration
        for name, player in players:
            player_registry[name] = player.serialize()

        dealer_expected = Dealer.deserialize([player_registry.values(), wh, deck])
        return dealer, dealer_expected

    def step4_case(self, configuration, step4, expected_configuration):

        dealer, dealer_expected = self.generate_dealers(configuration, expected_configuration)
        dealer.step4(step4)

        self.assertDealerEqual(dealer, dealer_expected)

    def test_start_with_no_species_perform_all_possible_actions(self):
        # no feeding occurs, wh is empty

        cards = [
            self.c(-3, "long-neck"),
            self.c(0, "long-neck"),
            self.c(1, "long-neck"),
            self.c(2, "long-neck"),
            self.c(3, "long-neck"),
            self.c(1, "carnivore"),
            self.c(1, "scavenger"),
            self.c(1, "fat-tissue"),
            self.c(-2, "long-neck"),
        ]

        step4 = [
            Actions(0, [GrowPopulation(0, 1)], [GrowBody(1, 2)],
                    [BoardTransfer(3, []), BoardTransfer(4, [5, 6, 7])], [ReplaceTrait(1, 1, 8)])
        ]

        configuration = [
            [("changed", Player(1, species=[], bag=10, cards=cards, external=DummyPlayer())),
             ("unchanged1", Player(2, species=[], bag=40, cards=[], external=DummyPlayer())),
             ("unchanged2", Player(3, species=[], bag=1, cards=[], external=DummyPlayer()))],
            2,
            []
        ]

        s0_exp = Species(food=0, population=2, body=0, traits=[])
        s1_exp = Species(food=0, population=1, body=1, traits=[Trait.CARNIVORE, Trait.LONG_NECK, Trait.FAT_TISSUE])

        configuration_expected = [
            [("changed", Player(1, species=[s0_exp, s1_exp], bag=10, cards=[]))],
            0,
            []
        ]

        self.step4_case(configuration, step4, configuration_expected)

    def test_start_with_no_species_perform_all_possible_actions_with_feeding(self):

        cards = [
            self.c(-3, "long-neck"),
            self.c(0, "long-neck"),
            self.c(1, "long-neck"),
            self.c(2, "long-neck"),
            self.c(3, "long-neck"),
            self.c(1, "carnivore"),
            self.c(1, "scavenger"),
            self.c(1, "fat-tissue"),
            self.c(-2, "long-neck"),
        ]

        step4 = [
            Actions.deserialize([0, [["population", 0, 1]], [["body", 1, 2]], [[3], [4, 5, 6, 7]], [[1, 1, 8]]]),
            Actions.deserialize([0, [], [], [], []]),
            Actions.deserialize([0, [], [], [], []]),
        ]

        configuration = [
            [("new_species", Player(1, species=[], bag=10, cards=cards, external=DummyPlayer())),
             ("1", Player(2, species=[], bag=40, cards=[self.c(8, "carnivore")], external=DummyPlayer())),
             ("2", Player(3, species=[], bag=1, cards=[self.c(-8, "carnivore")], external=DummyPlayer()))],
            10,
            []
        ]

        s0_exp = Species(food=2, population=2, body=0, traits=[])
        s1_exp = Species(food=1, population=1, body=1, fat_food=1,
                         traits=[Trait.CARNIVORE, Trait.LONG_NECK, Trait.FAT_TISSUE])

        configuration_expected = [
            [("new_species", Player(1, species=[s0_exp, s1_exp], bag=10, cards=[], external=DummyPlayer())),
             ("1", Player(2, species=[], bag=40, cards=[], external=DummyPlayer())),
             ("2", Player(3, species=[], bag=1, cards=[], external=DummyPlayer()))],
            (10 - 3 + 8 - 8 - 2 - 2),  # wh + discard0 + discard1 + discard2 - fat tissue on 1 - food on 0
            []
        ]

        self.step4_case(configuration, step4, configuration_expected)

    def test_start_with_species_with_cooperation_and_long_neck_and_foraging(self):

        cards = [
            self.c(-3, "symbiosis"),
            self.c(1, "scavenger"),
        ]

        step4 = [
            Actions.deserialize([1, [], [], [], [[0, 0, 0]]]),
            Actions.deserialize([0, [], [], [], []]),
            Actions.deserialize([0, [], [], [], []]),
        ]

        s0_start = Species(food=1, population=3, body=3, traits=[Trait.COOPERATION, Trait.LONG_NECK, Trait.FORAGING])
        s1_start = Species(food=1, body=2, population=2, traits=[])

        configuration = [
            [("replacement_symbiosis", Player(1, species=[s0_start, s1_start], bag=10, cards=cards,
                                              external=DummyPlayer())),
             ("1", Player(2, species=[], bag=1, cards=[self.c(8, "carnivore")], external=DummyPlayer())),
             ("2", Player(3, species=[], bag=1, cards=[self.c(-8, "carnivore")], external=DummyPlayer))],
            10,
            []
        ]

        s0_exp = Species(food=3, population=3, body=3, traits=[Trait.SYMBIOSIS, Trait.LONG_NECK, Trait.FORAGING])
        s1_exp = Species(food=2, body=2, population=2, traits=[])

        configuration_expected = [
            [("replacement_symbiosis", Player(1, species=[s0_exp, s1_exp], bag=10, cards=[], external=DummyPlayer())),
             ("1", Player(2, species=[], bag=1, cards=[], external=DummyPlayer())),
             ("2", Player(3, species=[], bag=1, cards=[], external=DummyPlayer()))],
            (10 + 1 - 3),  # wh + discard - food given (3: 2 because of long_neck, 1 because of cooperation)
            []
        ]

        self.step4_case(configuration, step4, configuration_expected)

    def test_individual_board_transfer(self):

        cards = [
            self.c(-3, "long-neck"),
            self.c(0, "long-neck"),
            self.c(1, "long-neck"),
            self.c(2, "warning-call"),
            self.c(3, "long-neck"),
            self.c(1, "carnivore"),
            self.c(1, "scavenger"),
            self.c(1, "fat-tissue"),
            self.c(-2, "long-neck"),
        ]

        step4 = [
            Actions.deserialize([0, [], [], [[2, 3, 1]], []]),
            Actions.deserialize([0, [], [], [], []]),
            Actions.deserialize([0, [], [], [], []]),
        ]

        s0_start = Species(food=3, body=3, population=3, traits=[])
        s1_start = Species(food=2, body=2, population=2, traits=[])

        configuration = [
            [("board_transferred", Player(1, species=[s0_start, s1_start], bag=10, cards=cards)),
             ("1", Player(2, species=[], bag=40, cards=[self.c(8, "carnivore")])),
             ("2", Player(3, species=[], bag=1, cards=[self.c(-8, "carnivore")]))],
            10,
            []
        ]

        s0_exp = Species(food=3, body=3, population=3, traits=[])
        s1_exp = Species(food=2, body=2, population=2, traits=[])
        s2_exp = Species(food=1, traits=[Trait.WARNING_CALL, Trait.LONG_NECK])

        cards_after = [
            self.c(3, "long-neck"),
            self.c(1, "carnivore"),
            self.c(1, "scavenger"),
            self.c(1, "fat-tissue"),
            self.c(-2, "long-neck"),
        ]

        configuration_expected = [
            [("board_transferred", Player(1, species=[s0_exp, s1_exp, s2_exp], bag=10, cards=cards_after)),
             ("1", Player(2, species=[], bag=40, cards=[])),
             ("2", Player(3, species=[], bag=1, cards=[]))],
            (10 - 3 + 8 - 8 - 1),  # wh + discard0 + discard1 + discard2 - feeding new species
            []
        ]

        self.step4_case(configuration, step4, configuration_expected)

    def test_individual_grow_population(self):

        cards = [
            self.c(-3, "long-neck"),
            self.c(0, "long-neck"),
        ]

        step4 = [
            Actions.deserialize([0, [["population", 0, 1]], [], [], []]),
            Actions.deserialize([0, [], [], [], []]),
            Actions.deserialize([0, [], [], [], []]),
        ]

        s0_start = Species(food=3, body=3, population=3, traits=[])
        s1_start = Species(food=2, body=2, population=2, traits=[])

        configuration = [
            [("population_grown", Player(1, species=[s0_start, s1_start], bag=10, cards=cards)),
             ("1", Player(2, species=[], bag=40, cards=[self.c(8, "carnivore")])),
             ("2", Player(3, species=[], bag=1, cards=[self.c(-8, "carnivore")]))],
            10,
            []
        ]

        s0_exp = Species(food=4, body=3, population=4, traits=[])
        s1_exp = Species(food=2, body=2, population=2, traits=[])

        configuration_expected = [
            [("population_grown", Player(1, species=[s0_exp, s1_exp], bag=10, cards=[])),
             ("1", Player(2, species=[], bag=40, cards=[])),
             ("2", Player(3, species=[], bag=1, cards=[]))],
            (10 - 3 + 8 - 8 - 1),  # wh + discard0 + discard1 + discard2 - feeding species grown
            []
        ]

        self.step4_case(configuration, step4, configuration_expected)

    def test_individual_grow_body(self):

        cards = [
            self.c(-3, "long-neck"),
            self.c(0, "long-neck"),
        ]

        step4 = [
            Actions.deserialize([0, [], [["body", 0, 1]], [], []]),
            Actions.deserialize([0, [], [], [], []]),
            Actions.deserialize([0, [], [], [], []]),
        ]

        s0_start = Species(food=3, body=3, population=3, traits=[])
        s1_start = Species(food=2, body=2, population=2, traits=[])

        configuration = [
            [("body_grown", Player(1, species=[s0_start, s1_start], bag=10, cards=cards)),
             ("1", Player(2, species=[], bag=40, cards=[self.c(8, "carnivore")])),
             ("2", Player(3, species=[], bag=1, cards=[self.c(-8, "carnivore")]))],
            10,
            []
        ]

        s0_exp = Species(food=3, body=4, population=3, traits=[])
        s1_exp = Species(food=2, body=2, population=2, traits=[])

        configuration_expected = [
            [("body_grown", Player(1, species=[s0_exp, s1_exp], bag=10, cards=[])),
             ("1", Player(2, species=[], bag=40, cards=[])),
             ("2", Player(3, species=[], bag=1, cards=[]))],
            (10 - 3 + 8 - 8),  # wh + discard0 + discard1 + discard2
            []
        ]

        self.step4_case(configuration, step4, configuration_expected)

    def test_individual_replace_trait(self):

        cards = [
            self.c(-3, "long-neck"),
            self.c(0, "long-neck"),
        ]

        step4 = [
            Actions.deserialize([1, [], [], [], [[0, 0, 0]]]),
            Actions.deserialize([0, [], [], [], []]),
            Actions.deserialize([0, [], [], [], []]),
        ]

        s0_start = Species(food=3, body=3, population=3, traits=[Trait.CARNIVORE])
        s1_start = Species(food=2, body=2, population=2, traits=[])

        configuration = [
            [("body_grown", Player(1, species=[s0_start, s1_start], bag=10, cards=cards)),
             ("1", Player(2, species=[], bag=40, cards=[self.c(8, "carnivore")])),
             ("2", Player(3, species=[], bag=1, cards=[self.c(-8, "carnivore")]))],
            10,
            []
        ]

        s0_exp = Species(food=3, body=3, population=3, traits=[Trait.LONG_NECK])
        s1_exp = Species(food=2, body=2, population=2, traits=[])

        configuration_expected = [
            [("body_grown", Player(1, species=[s0_exp, s1_exp], bag=10, cards=[])),
             ("1", Player(2, species=[], bag=40, cards=[])),
             ("2", Player(3, species=[], bag=1, cards=[]))],
            (10 + 0 + 8 - 8),  # wh + discard0 + discard1 + discard2
            []
        ]

        self.step4_case(configuration, step4, configuration_expected)

    def test_transfer_food_from_fat_tissue(self):

        cards = [
            self.c(-3, "long-neck"),
        ]

        step4 = [
            Actions.deserialize([0, [], [], [], []]),
            Actions.deserialize([0, [], [], [], []]),
            Actions.deserialize([0, [], [], [], []]),
        ]

        s0 = Species(food=0, population=2, body=4, traits=[Trait.FAT_TISSUE], fat_food=3)

        configuration = [
            [("fat-tissue", Player(1, species=[s0], bag=10, cards=cards)),
             ("1", Player(2, species=[], bag=40, cards=[self.c(8, "carnivore")])),
             ("2", Player(3, species=[], bag=1, cards=[self.c(-8, "carnivore")]))],
            4,
            []
        ]

        # s0 gets 2 tokens from fat tissue and stores 1 remaining token on wh on fat tissue
        s0_exp = Species(food=2, population=2, body=4, traits=[Trait.FAT_TISSUE], fat_food=2)

        configuration_expected = [
            [("fat-tissue", Player(1, species=[s0_exp], bag=10, cards=[])),
             ("1", Player(2, species=[], bag=40, cards=[])),
             ("2", Player(3, species=[], bag=1, cards=[]))],
            (4 - 3 + 8 - 8 - 1),  # wh + discard0 + discard1 + discard2 - fat tissue on 1
            []
        ]

        self.step4_case(configuration, step4, configuration_expected)


def generate_json_files():

    def json_generator(n, configuration, step4, configuration_expected):
        dealer, dealer_expected = Step4TestCase.generate_dealers(configuration, configuration_expected)
        in_data = [dealer.serialize(), [a.serialize() for a in step4]]
        out_data = dealer_expected.serialize()

        with open("tests/{}-in.json".format(n), "w") as test_in:
            json.dump(in_data, test_in)
        with open("tests/{}-out.json".format(n), "w") as test_out:
            json.dump(out_data, test_out)

    test_generator = Step4TestCase()

    test_methods = [attr for attr in Step4TestCase.__dict__ if attr.startswith("test_")]
    for test_number, method in enumerate(test_methods):
        print("Generating test {} based on {}".format(test_number, method))
        test_generator.step4_case = partial(json_generator, test_number)
        getattr(Step4TestCase, method)(test_generator)


if __name__ == "__main__":
    generate_json_files()
