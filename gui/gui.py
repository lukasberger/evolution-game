"""

    GUI Classes and helpers for the Evolution Game

"""

from tkinter import *


class GUI:
    """ Contains functionality for GUI representation of the various Evolution models. """

    NEWLINE = "\n"
    INDENTATION = "\t"
    SEPARATOR = ", "

    WINDOW_TITLE_DEALER = "Dealer"
    WINDOW_TITLE_PLAYER = "Player"

    WINDOW_WIDTH = 800
    WINDOW_HEIGHT = 800

    DEALER_KEY_WATERING_HOLE = "watering-hole"
    DEALER_KEY_PLAYERS = "players"
    DEALER_KEY_DECK = "deck"

    DEALER_TEMPLATE = """{watering_hole_key}: {{watering_hole_data}}
{players_key}:
{{players_data}}
{deck_key}:
{{deck_data}}""".format(watering_hole_key=DEALER_KEY_WATERING_HOLE,
                        players_key=DEALER_KEY_PLAYERS,
                        deck_key=DEALER_KEY_DECK)

    SPECIES_KEY_FOOD = "food"
    SPECIES_KEY_BODY = "body"
    SPECIES_KEY_POPULATION = "population"
    SPECIES_KEY_TRAITS = "traits"
    SPECIES_KEY_FAT_FOOD = "fat-food"

    SPECIES_TEMPLATE = """{food_key}: {{food_data}}, {body_key}: {{body_data}}, {population_key}: {{population_data}}
{traits_key}: {{traits_data}}
""".format(food_key=SPECIES_KEY_FOOD,
           body_key=SPECIES_KEY_BODY,
           population_key=SPECIES_KEY_POPULATION,
           traits_key=SPECIES_KEY_TRAITS)

    SPECIES_TEMPLATE_FAT = """{food_key}: {{food_data}}, {body_key}: {{body_data}}, {population_key}: {{population_data}}, {fat_key}: {{fat_data}}
{traits_key}: {{traits_data}}
""".format(food_key=SPECIES_KEY_FOOD,
           body_key=SPECIES_KEY_BODY,
           population_key=SPECIES_KEY_POPULATION,
           fat_key=SPECIES_KEY_FAT_FOOD,
           traits_key=SPECIES_KEY_TRAITS)

    TRAIT_CARD_KEY_VALUE = "value"
    TRAIT_CARD_KEY_TRAIT = "trait"

    TRAIT_CARD_TEMPLATE = "({value}, {trait})"

    PLAYER_KEY_ID = "id"
    PLAYER_KEY_BAG = "bag"
    PLAYER_KEY_SPECIES = "species"
    PLAYER_KEY_CARDS = "cards"

    PLAYER_TEMPLATE = """Player {id_key}: {{id_data}}, {bag_key}: {{bag_data}}
    {species_key}:
{{species_data}}
    {cards_key}:
{{cards_data}}
""".format(id_key=PLAYER_KEY_ID,
           bag_key=PLAYER_KEY_BAG,
           species_key=PLAYER_KEY_SPECIES,
           cards_key=PLAYER_KEY_CARDS)

    @classmethod
    def indent(cls, string, n=1):
        """ Indents each line in the given string by n indents
        :param string: string to indent
        :param n: number of indentations
        :return: indented string
        """
        indentation = cls.INDENTATION * n
        return cls.NEWLINE.join([indentation + line for line in string.split(cls.NEWLINE)])

    @classmethod
    def render_dealer(cls, data):
        """ Creates a text representation of the dealer from the given dealer data.
        :param data: dealer data returned by the dealer's display method
        :return: text rendering of the dealer
        """
        watering_hole_data = data[cls.DEALER_KEY_WATERING_HOLE]
        players_data = data[cls.DEALER_KEY_PLAYERS]
        deck_data = data[cls.DEALER_KEY_DECK]

        players_rendering = [cls.render_player(p) for p in players_data]
        deck_rendering = [cls.render_trait_card(tc) for tc in deck_data]

        players_indented = cls.NEWLINE.join([cls.indent(p) for p in players_rendering])
        deck_indented = cls.INDENTATION + cls.SEPARATOR.join(deck_rendering)

        return cls.DEALER_TEMPLATE.format(watering_hole_data=watering_hole_data,
                                          players_data=players_indented,
                                          deck_data=deck_indented)

    @classmethod
    def render_player(cls, data):
        """ Creates a text representation of the player from the given player data.
        :param data: player data returned by the player's display method
        :return: text rendering of the player
        """
        id_data = data[cls.PLAYER_KEY_ID]
        bag_data = data[cls.PLAYER_KEY_BAG]

        species_data= data[cls.PLAYER_KEY_SPECIES]
        cards_data = data[cls.PLAYER_KEY_CARDS]

        species_rendering = [cls.render_species(s) for s in species_data]
        cards_rendering = [cls.render_trait_card(tc) for tc in cards_data]

        species_indented = cls.NEWLINE.join([cls.indent(s, 2) for s in species_rendering])
        cards_indented = cls.INDENTATION + cls.SEPARATOR.join(cards_rendering)

        return cls.PLAYER_TEMPLATE.format(id_data=id_data,
                                          bag_data=bag_data,
                                          species_data=species_indented,
                                          cards_data=cards_indented)


    @classmethod
    def render_species(cls, data):
        """ Creates a text representation of the species from the given species data.
        :param data: species data returned by the species's display method
        :return: text rendering of the species
        """
        parameters = {
            'food_data': data[cls.SPECIES_KEY_FOOD],
            'body_data': data[cls.SPECIES_KEY_BODY],
            'population_data': data[cls.SPECIES_KEY_POPULATION],
            'traits_data': data[cls.SPECIES_KEY_TRAITS],
        }

        if cls.SPECIES_KEY_FAT_FOOD in data:
            parameters['fat_data'] = data[cls.SPECIES_KEY_FAT_FOOD]
            return cls.SPECIES_TEMPLATE_FAT.format(**parameters)
        else:
            return cls.SPECIES_TEMPLATE.format(**parameters)

    @classmethod
    def render_trait_card(cls, data):
        """ Creates a text representation of the trait card from the given trait card data.
        :param data: trait card data returned by the trait card's display method
        :return: text rendering of the trait card
        """
        value = data[cls.TRAIT_CARD_KEY_VALUE]
        trait = data[cls.TRAIT_CARD_KEY_TRAIT]
        return cls.TRAIT_CARD_TEMPLATE.format(value=value, trait=trait)

    @classmethod
    def create_window(cls, title, data):
        """ Creates a new tkinter window with the given title and renders the given test in a scrollable text view.
        :param title: title of the window
        :param data: text to display in the window
        :return: None
        """
        root = Tk()
        root.title(title)
        root.geometry("{}x{}".format(cls.WINDOW_WIDTH, cls.WINDOW_HEIGHT))

        text = Text(root, state="normal", wrap="word")
        text.insert(INSERT, data)
        text.configure(state="disabled")

        vsb = Scrollbar(root, command=text.yview, orient="vertical")
        vsb.pack(side="right", fill="y")

        text.configure(yscrollcommand=vsb.set)
        text.pack(expand=True, fill="both")

        root.mainloop()

    @classmethod
    def dealer_window(cls, data):
        """ Creates a new dealer window with a rendering of the dealer state based on the given data
        :param data: dealer representation returned by the display method
        """
        rendering = cls.render_dealer(data)
        cls.create_window(cls.WINDOW_TITLE_DEALER, rendering)

    @classmethod
    def player_window(cls, data):
        """ Creates a new player window with a rendering of the player state based on the given data
        :param data: player representation returned by the display method
        """
        rendering = cls.render_player(data)
        cls.create_window(cls.WINDOW_TITLE_PLAYER, rendering)


def render_dealer(data):
    """ Opens a new window with a rendering of the dealer based on the given data
    :param data: dealer representation returned by the display method
    """
    GUI.dealer_window(data)

def render_player(data):
    """ Opens a new window with a rendering of the player based on the given data
    :param data: player representation returned by the display method
    """
    GUI.player_window(data)
