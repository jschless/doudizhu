import pytest
import time

def test_create_game(client, auth):
    auth.login()
    assert client.get('/').status_code == 200
    response = client.post(
        '/', data={'create': 'Create Game'}, follow_redirects=True)

    assert response._status_code == 200


def test_connection_and_add_to_db(app, client, socketio_server, auth):
    test_game = "XM1P8"
    data = {'game_id': test_game, 'username': 'testing'}
    auth.login()
    response = client.post('/', 
        data={'join': 'Join Game', 'gamecode': test_game}, 
        follow_redirects=True)

    socket_client = socketio_server.test_client(app, flask_test_client=client)

    assert socket_client.is_connected() == True
    socket_client.emit('add to database', data)

    for m in socket_client.get_received():
        if m['name'] == 'update_gameboard':
            assert 'testing' in m['args'][0]['usernames']
        elif m['name'] == 'message':
            assert f"successfully added {data['username']} to database" == m['args']