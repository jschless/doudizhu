import pytest


def test_create_game(client, auth):
    auth.login()
    assert client.get('/').status_code == 200
    response = client.post(
        '/', data={'create': 'Create Game'}, follow_redirects=True)

    print(response.headers, response.data)
    assert response == True

# from selenium.webdriver import Chrome
# import pytest

# with Chrome(executable_path='/home/joe/chromedriver/chromedriver') as driver:
#     driver.get('http://127.0.0.1:5000/')
