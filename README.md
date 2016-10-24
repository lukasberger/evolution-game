# Evolution game simulator

This project implements a simulator of a modified version of the [Evolution](http://www.northstargames.com/products/evolution) game for the CS4500 – Software Development class. It contains both server and client implementations and allows for networked games.

Structure of the repository:

    /documentation/:
        Dependency Diagram.png: Diagram presenting dependencies of different classes
        internal_protocol.txt: Internal protocol description
        remote_protocol.txt: Remote protocol description
        Relationship Diagram.png: Diagram presenting relationships between classes' attributes
    /evolution/: Files related to the core of Evolution
        /common/: Files shared by both the Dealer and Player
            actions.py: Implements Action4 and its individual subactions
            feeding_outcome.py: Classes for all possible outcomes for the Player's feed species method.
            player_helpers.py: Contains helpers for communication between Players
            remote_actor.py: Implements a mixin for remote communication
            species.py: Represents a Species Board
            trait.py: Represents an Enumeration for the possible Traits
            trait_card.py: Represents a TraitCard
        /dealer/: Files used by the Dealer
            dealer.py: The Dealer representation
            remote_dealer.py: The Remote Dealer representation
        /player/: Files pertaining to the Players
            base_player.py: Base Player for Evolution
            dummy_player.py: Player implementing Dummy strategy
            external_player.py: External Player Interface
            player.py: Represents a Player (as seen by a Dealer)
            remote_player.py: Remote Proxy for a networked Player
            strategy_player.py: External Player that implements a strategy
        data_definitions.py: Codifies Evolution data definitions
    /test_harnesses/: Test Harnesses, related JSON test files, and other test-related files
    client: Used to execute client.py
    client.py: Implements Evolution Client with Silly Player strategy
    server: Used to execute server.py
    server.py: Launches an Evolution Server.

To run the Server (defaults to 127.0.0.1:45679):
```
./server  
./server --host HOST --port PORT
./server -i HOST -p PORT
```

To run the Client (defaults to 127.0.0.1:45679)
```
./client
./client --host HOST --port PORT
./client -i HOST -p PORT
```

Tests can be run from the base directory if nose is installed with
```
nosetests evolution
```

A test that compares the output of sequential and remote main can be run with
```
nosetests test_main.py
```

Individual test harnesses can be ran from inside of the test_harnesses directory with run_tests.sh:
```
./run_tests.sh x{name} x{name}_tests
```
