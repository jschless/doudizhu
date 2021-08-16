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
