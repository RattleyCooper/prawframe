from threading import Thread
from time import sleep
import socket
from configparser import ConfigParser
from os import getcwd

try:
    from prawframe.server_connection import HeaderServer
    from prawframe.common_connection import scrambles_input_unscrambles_output
except ImportError:
    from .common_connection import scrambles_input_unscrambles_output
    from .server_connection import HeaderServer


class Connection(object):
    pool = []


class Server(object):
    socket = None
    shutdown = False
    alive = False


def listener(sock):
    Server.alive = True
    while not Server.shutdown:
        try:
            conn, address = sock.accept()
        except socket.error as e:
            # Loop indefinitely
            continue

        if (conn, address) not in Connection.pool:
            Connection.pool.append((conn, address))

    for conn, address in Connection.pool:
        conn.close()

    Server.alive = False


def setup(host, port):
    sock = socket.socket()
    sock.setblocking(True)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))
    sock.listen(1)
    Server.socket = sock

    thread = Thread(
        name='listener',
        target=listener,
        args=[sock]
    )

    thread.start()

    while not Connection.pool:
        sleep(0.05)

    conn = Connection.pool.pop()[0]

    server = HeaderServer(conn, (host, port))

    # Wrap the server.send_command
    send_command = scrambles_input_unscrambles_output(server.send_command)

    while not Server.shutdown:
        inp = input('>>> ')

        if inp.strip() == '':
            continue

        resp = send_command(inp)

        print(resp)

        if inp == 'exit':
            Server.shutdown = True
            break

    while Server.alive:
        sleep(0.05)

    thread.join()


config = ConfigParser()
config.read('{}/.env'.format(getcwd()))
setup(config['Console']['Host'], int(config['Console']['Port']))
