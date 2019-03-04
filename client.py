import sys
from code import InteractiveConsole

try:
    from prawframe.client_connection import HeaderClient
    from prawframe.output import PrintQueue, Msg
    from prawframe.pluginlib import BasePlugin
    from prawframe.common_connection import unscrambles_output
    from prawframe.common_connection import scrambles_input
except ImportError:
    from .client_connection import HeaderClient
    from .output import PrintQueue, Msg
    from .pluginlib import BasePlugin
    from .common_connection import unscrambles_output
    from .common_connection import scrambles_input


class FileCache:
    """
    Cache the stdout/stderr text so we can analyze it before returning it.
    """
    def __init__(self):
        self.out = []
        self.reset()

    def reset(self):
        self.out = []

    def write(self, line):
        self.out.append(line)

    def flush(self):
        output = ''.join(self.out)
        self.reset()
        return output


class Shell(InteractiveConsole):
    """
    Wrapper around InteractiveConsole so stdout and stderr can be intercepted easily.
    """
    def __init__(self, locals=None, filename='<console>'):
        self.stdout = sys.stdout
        self.stderr = sys.stderr
        self.cache = FileCache()
        super(Shell, self).__init__(locals=locals, filename=filename)
        return

    def get_output(self):
        sys.stdout = self.cache
        sys.stderr = self.cache

    def return_output(self):
        sys.stdout = self.stdout
        sys.stderr = self.stderr

    def push(self, line):
        self.get_output()
        InteractiveConsole.push(self, line)
        self.return_output()
        output = self.cache.flush().strip()
        print(output)
        return output


class Client(object):
    restart = False
    alive = False
    shutdown = False

    bot = None


def main_client_loop(client):
    _locals = {
        'Client': Client,
        'Bot': Client.bot,
        '__file__': __file__,
        '__name__': __name__,
        '__package__': __package__
    }

    # Create shortcuts for plugins.
    # for attr in dir(plugins):
    #     obj = getattr(plugins, attr)
    #     try:
    #         if issubclass(obj, BasePlugin):
    #             _locals[obj.__name__] = obj
    #             if obj.shorthand:
    #                 _locals[obj.shorthand] = obj
    #     except TypeError:
    #         continue

    console = Shell(filename='< Remote Python Console >', locals=_locals)
    receive_data = unscrambles_output(client.receive_data)
    send_data = scrambles_input(client.send_data)
    while not Client.restart:
        d = receive_data()

        if d.strip().lower() == 'exit':
            send_data('Goodbye for now!')
            Client.restart = True
            client.sock.shutdown(1)
            client.sock.close()
            break

        elif d == '':
            continue

        command = d
        try:
            output = console.push(command)
            # eval(command)
            send_data(output)
            continue
        except Exception as e:
            send_data('{}'.format(e))
            continue
        # client.send_data('...')


def run_command_client(host, port):
    PrintQueue.push(Msg('Starting command client...'))
    client = None
    while not Client.shutdown:
        Client.restart = False
        Client.shutdown = False
        Client.alive = True

        client = HeaderClient(host, port, echo=False)
        client.connect_to_server()
        main_client_loop(client)

    if client:
        client.sock.shutdown(1)
        client.sock.close()

    Client.alive = False


if __name__ == '__main__':
    pass
