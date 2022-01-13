This project is an English-language web server and UI for playing Dou Dizhu. The webstack is Flask, MongoDB, and SocketIO. The front end is hacked together using vanilla JS/CSS/HTML and jQuery. 

## Design
todo 

## Development
To get started and run this project locally, first clone it:

1. Set yourself up Make sure you have a running MongoDB server. This can be local or a Mongo Atlas connection. For local:

```bash sudo service mongod start && mongod```

Create an environment variable for the correct Mongo URI:

```bash export mongodb_uri = "mongodb://localhost:27017/"```


2. Set Flask environmental variables:

```bash 
export FLASK_APP=flaskr
export FLASK_ENV=development
python -m flaskr
```

## Bugs
- Add resilience in case someone refreshes or disconnect (this involves resending messages or tracking the entire gamestate)
- Before sending to a socket... check if it exists... remove players that left
- A million timers are created

## Features
- Animation: rattle (shake)
- Spring-light
- Suggested move 
- Blind remains in the middle, player knows which of his cards are visible
- At end of round, show entire hand (with used cards greyed out, perhaps)
