from . import socketio


def send_socket(message: str, data, address=None):
    socketio.emit(message, data, to=address)


def flash_message(message: str, address=None, event="flash") -> None:
    """Displays a notification in red at the top of the client

    event: "flash" -> rewrite to flash, "flash append" -> append toflash
    player: pass players dict if you want to flash to a specific user
    """
    if address:
        socketio.emit(event, message, to=address)
    else:
        socketio.emit(event, message)
