import eventlet
eventlet.monkey_patch()

from flask import Flask, request, render_template
from flask_socketio import SocketIO, send, emit, join_room
from ee_modules.landscape.fractal_landscape_numpy import build_landscape
import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'



socketio = SocketIO(app, async_mode='eventlet')

all_users = []
user_count = 0


@app.route('/hello')
def index():
    return 'Welcome to Ethereal Epoch'

# Setup
def send_new_user_terrain():
    print('Build Terrain')
    seed = datetime.datetime.now()
    seed = seed.hour + 24 * (seed.day + 31 * seed.month)
    emit('load', {'terrain':build_landscape(250, 250, seed=100000 + seed).tolist()}, room=request.sid) # emits just to new connecting user

def send_users_to_new_user(): 
    for player in all_users:
        print('call spawn event', player)
        # add check for already exists
        request_position(); 
        emit('spawn', {"id": player}, room=request.sid)

def request_position(): 
    print('call request position', request.sid)
    emit('requestPosition', {},  broadcast=True)

@socketio.on('connect')
def test_connect():
    global all_users, user_count
    print('connect with socket info', request.sid)
    user_count += 1
    send_users_to_new_user()
    all_users.append(request.sid)
    send_new_user_terrain()
    emit('spawn', {'id': request.sid, 'count': user_count}, broadcast=True, include_self=False)

@socketio.on('move')
def share_user_movement(json): 
    print('send user movement to other users' + str(json) + request.sid)
    x = json["x"]
    y = json["y"]
    z = json["z"]
    emit('playerMove', {'id': request.sid, 'x': x, 'y': y, 'z': z}, broadcast=True, include_self=False)

@socketio.on('playerPosition')
def send_position_to_new_user(json):
    print('called this', json); 
    x = json["x"]
    y = json["y"]
    z = json["z"]
    print('this should really only go to new user', request.sid, x, y, z); 
    emit('updatePosition', {"id": request.sid, "x": x, "y": y, "z": z}, broadcast=True)

# disconnect 

@socketio.on('disconnect')
def disconnect():
    print('Client disconnected', request.sid)
    global user_count
    user_count -= 1
    all_users.remove(request.sid)
    emit('onEndSpawn', {'id': request.sid}, broadcast=True) # currently doens't de-render user

# error handling
@socketio.on_error()    
def error_handler(e):
    print('error', e)
    pass

@socketio.on_error_default
def default_error_handler(e):
    print('error', e)
    pass


if __name__ == '__main__':
    # socketio.run(app)
    eventlet.wsgi.server(eventlet.listen(('', 6000)), app, debug=True)
