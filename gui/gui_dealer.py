import os
import sys
import json

from gui import render_dealer

PROJECT_ROOT = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")
sys.path.insert(0, PROJECT_ROOT)

from evolution.dealer.dealer import Dealer


def main():
    configuration = json.load(sys.stdin)
    dealer = Dealer.deserialize(configuration)
    render_dealer(dealer.display())

if __name__ == "__main__":
    main()
