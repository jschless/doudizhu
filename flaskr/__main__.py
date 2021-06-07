if __name__ == "__main__":
    from . import app, socketio
    socketio.run(app)