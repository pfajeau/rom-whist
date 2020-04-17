import romwhist
from romwhist import app, socketio

if __name__ == '__main__':
    app = romwhist.create_app()
    socketio.run(app, debug=True)
