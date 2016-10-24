"""
    Represents a Trait in the Evolution game

"""

from enum import Enum


# how much bigger the body size of an attacker must be when attacking a species with hard-shell
HARD_SHELL_THRESHOLD = 4
# amount of damage cause by horns
HORNS_DAMAGE = 1

traits = [
    "carnivore",
    "ambush",
    "burrowing",
    "climbing",
    "cooperation",
    "fat-tissue",
    "fertile",
    "foraging",
    "hard-shell",
    "herding",
    "horns",
    "long-neck",
    "pack-hunting",
    "scavenger",
    "symbiosis",
    "warning-call",
]


class TraitEnum(Enum):

    def __repr__(self):
        return "Trait(\"{}\")".format(self.value)

    def __str__(self):
        return self.value

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.value == other.value

    def __lt__(self, other):
        return self.value < other.value

    def __hash__(self):
        return hash(self.value)


Trait = TraitEnum("Trait", names={trait.replace("-", "_").upper(): trait for trait in traits})
