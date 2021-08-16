if __name__ == "__main__":
    from . import app, socketio, login_manager
    login_manager.init_app(app)
    socketio.run(app)