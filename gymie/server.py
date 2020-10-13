import json
import eventlet
from eventlet import wsgi, websocket
from .api import methods
from .exceptions import *


#####################################
# WebSocket Server API and Handlers #
#####################################

def message_handle(ws, message):
    try:
        data = json.loads(message)
        method = data['method']
        params = data['params']
    except json.JSONDecodeError:
        ws.close((1003, 'Message `{}` is invalid'.format(message)))
    except KeyError:
        keys = str(list(data.keys()))
        ws.close((1003, 'Message keys {} are missing or invalid'.format(keys)))
    else:
        try:
            methods[method](ws, **params)
        except KeyError:
            ws.close((1007, 'Method `{}` not found'.format(method)))
        except TypeError:
            ws.close((1007, 'Parameters `{}` are wrong'.format(data['params'])))
        except InstanceNotFound as instance_id:
            ws.close((1007, 'Instance `{}` not found'.format(instance_id)))
        except EnvironmentMalformed as env_id:
            ws.close((1007, 'Environment `{}` is malformed'.format(env_id)))
        except EnvironmentNotFound as env_id:
            ws.close((1007, 'Environment `{}` not found'.format(env_id)))
        except WrongAction as action:
            ws.close((1007, 'Action `{}` is wrong'.format(action)))
        except Exception as err:
            ws.close((1007, 'Unknonwn error: {}'.format(err)))

@websocket.WebSocketWSGI
def gym_handle(ws):
    while True:
        message = ws.wait()
        if message is None: 
            break
        message_handle(ws, message)

def dispatch(environ, start_response):
    if environ['PATH_INFO'] == '/gym':
        return gym_handle(environ, start_response)
    else:
        start_response('200 OK', [('Content-Type', 'text/plain')])
        return ['Gymie is running...']

def start(host, port):
    try:
        listener = eventlet.listen((args.host, args.port), reuse_port=False)
    except OSError as err:
        print(f'Address http://{args.host}:{args.port} already in use')
    else:
        wsgi.server(listener, dispatch)
