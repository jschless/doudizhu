The idea here is to create a web application to play DDZ.

Steps: 
1. Design game logic in python.
2. Convert to flask app that can interface with web app.
3. Create front end.

## Design
I will use the Model-View-Controller framework. I

Classes:
- player: this contains relevant information for the player (name, cards, score)
- game: a game has multiple rounds
- round: a round starts with the dealing and goes until someone runs out of cards.
- hand: a hand is a sequence of plays
