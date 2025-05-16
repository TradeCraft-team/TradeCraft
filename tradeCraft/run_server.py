"""
MAIN ENTRY of tradeCraft
"""

from src.server import server_app, socketio

if __name__ == '__main__':
    # print('socketio run')
    socketio.run(server_app,
                 debug=False,
                 allow_unsafe_werkzeug=True,
                 host='0.0.0.0',
                 )
