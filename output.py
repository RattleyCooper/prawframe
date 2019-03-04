from datetime import datetime
from threading import Thread


def now():
    n = datetime.now()

    dt = (n.day, n.month, n.year, n.hour, n.minute, n.second)

    day, month, year, hour, minute, second = list(str(i).zfill(2) for i in dt)

    return '{}-{}-{} {}:{}:{}'.format(
        month,
        day,
        year,
        hour,
        minute,
        second
    )


def timestamp(function):
    def decorator(*args, **kwargs):
        if hasattr(args[0], 'start'):
            return function('{}{} {}'.format(args[0].start, now(), args[0]), *args[1:], **kwargs)

        return function('{} {}'.format(now(), args[0]), *args[1:], **kwargs)
    return decorator


tprint = timestamp(print)


class Msg(object):
    def __init__(self, message, end='\n', start='', stamp=True):
        self.body = message
        self.end = end
        self.stamp = stamp
        self.start = start

    def __len__(self):
        return len(self.body)

    def __str__(self):
        return self.body


class Messages(Msg):
    def __init__(self, messages, end=False):
        super(Messages, self).__init__(messages, end=end)
        self.body = messages
        self.group = messages
        self.end = end


class PrintQueueController(object):
    shutdown = False
    alive = False
    _locked = False


def waits_for_unlock(method):
    def decorator(*args, **kwargs):
        cls = args[0]

        # Wait until the object is not in use.
        while cls._locked:
            continue

        return_value = method(*args, **kwargs)
        return return_value

    return decorator


class PrintQueue(PrintQueueController):
    _items = []
    _listener_thread = None
    _last_message = Msg('')

    @classmethod
    def print_message(cls, message):
        if message.end != '\r' and cls._last_message.end == '\r':
            message.start = '\n'

        if message.stamp:
            tprint(message, end=message.end)
            cls._last_message = message
            return

        print(message, end=message.end)
        cls._last_message = message
        return

    @classmethod
    def _listener(cls):
        cls.alive = True
        while not cls.shutdown:
            while len(cls._items) < 1:
                continue

            while cls._locked:
                continue

            cls._locked = True

            try:
                message = cls._items.pop(0)
            except IndexError:
                cls._locked = False
                continue

            if isinstance(message, Messages):
                for message_obj in message.group:
                    cls.print_message(message_obj)
                cls._locked = False
                continue

            cls.print_message(message)
            cls._locked = False
        PrintQueueController.alive = False
        return

    @classmethod
    def listen(cls):
        cls._listener_thread = Thread(
            name='PrintQueue Listener',
            target=cls._listener
        )
        cls._listener_thread.start()
        return

    @classmethod
    @waits_for_unlock
    def push(cls, message, end='\n', start='', stamp=True):
        if isinstance(message, str):
            message = Msg(message, end=end, start=start, stamp=stamp)

        if not isinstance(message, Msg):
            raise TypeError('message must be an instance of `Msg`.')

        cls._items.append(message)

    @classmethod
    def lock(cls):
        cls._locked = True
        return

    @classmethod
    def unlock(cls):
        cls._locked = False
        return

    @classmethod
    @waits_for_unlock
    def join_thread(cls):
        cls._listener_thread.join()
        return


if __name__ == '__main__':
    from time import sleep

    pq = PrintQueue
    pq.listen()

    pq.push(Msg('Hello world'))
    pq.push(Messages([Msg('goodbye', end='\n'), Msg('world', end='\n')]))
    pq.push(Msg('what is that?'))

    def add_items(queue):
        x = 0
        while True:
            queue.push(Msg(str(x)))
            x += 1
            sleep(1)

    t = Thread(target=add_items, args=[pq])
    t.start()

    for i in range(0, 10000):
        pq.push(Msg(str(i), end='\r'))
        #sleep(0.0000001)

    t.join()
    pq.join_thread()
