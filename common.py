from datetime import datetime
from time import sleep
try:
    from prawframe.output import PrintQueue, Msg
except ImportError:
    from .output import PrintQueue, Msg


def bytes_packet(_bytes, termination_string=']'):
    """
    Create a packet containing the amount of bytes for the proceeding data.

    :param _bytes:
    :param termination_string:
    :return:
    """

    return '{}{}'.format(len(_bytes), termination_string)


def load_welcome_message():
    with open('welcome_message', 'r') as f:
        output = f.read()
        f.close()

    return output


def timestamp(function):
    def decorator(*args, **kwargs):
        if hasattr(args[0], 'start'):
            return function('{}{} {}'.format(args[0].start, now(), args[0]), *args[1:], **kwargs)

        return function('{} {}'.format(now(), args[0]), *args[1:], **kwargs)
    return decorator


tprint = timestamp(print)


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


class LoadingIcon(object):
    def __init__(self):
        self.state = False
        self.ticks = 0

    def load(self, end=''):
        ticks = end if end else str(self.ticks).zfill(3)
        PrintQueue.push(Msg('/ {}'.format(ticks) if self.state else '\\ {}'.format(ticks), end='\r'))
        self.state = False if self.state else True
        self.ticks += 1

    def reset_ticks(self):
        self.ticks = 0


class StaticLoadingIcon(object):
    state = 0
    ticks = 0

    @staticmethod
    def load(end=''):
        ticks = end if end else str(StaticLoadingIcon.ticks).zfill(3)

        icon = '-' if StaticLoadingIcon.ticks % 3 == 0 else False
        icon = '/' if not icon and StaticLoadingIcon.ticks % 2 == 0 else False
        icon = '\\' if not icon else icon

        line = '{} {}'.format(icon, ticks)
        PrintQueue.push(Msg(line, end='\r'))
        StaticLoadingIcon.state = False if StaticLoadingIcon.state else True

    @staticmethod
    def tick():
        StaticLoadingIcon.ticks += 1

    @staticmethod
    def reset_ticks():
        StaticLoadingIcon.ticks = 0


def thread_safe(method):
    """
    Decorator for creating thread-safe methods.  The object that the decorated method comes from
    must have a `_locked` attribute.

    :param method:
    :return:
    """
    def decorator(*args, **kwargs):
        cls = args[0]

        # Wait until the object is not in use.
        while cls._locked:
            sleep(0.05)

        # "Lock" the object
        cls._locked = True
        # Do the work
        return_value = method(*args, **kwargs)
        # Release the lock
        cls._locked = False

        return return_value

    return decorator


class TypeBound(object):
    def __init__(self):
        pass

    def __setattr__(self, key, value):
        """
        This magic method binds attributes to their original type!

        :param key:
        :param value:
        :return:
        """

        # Check the key to see if it's in the list of attributes that
        # must be a specific type and raise a TypeError if the value's
        # type does not match the specified type.
        lock_obj = getattr(self, key)

        if type(value) == set and type(lock_obj) == set:
            object.__setattr__(self, key, value)
            return

        primitive_types = (
            int, str, float, bool, list, tuple, dict
        )
        if isinstance(value, primitive_types):
            try:
                key_check = isinstance(value, lock_obj)
            except TypeError:
                if type(value) is not type(lock_obj):
                    err_msg = 'Cannot set "{}" because it is the incorrect got: {} expects: {}'.format(
                        key,
                        str(value),
                        str(lock_obj)
                    )
                    raise TypeError(err_msg)

            object.__setattr__(self, key, value)
            return

        try:
            if isinstance(value, lock_obj):
                object.__setattr__(self, key, value)
                return
        except TypeError:
            if isinstance(value, lock_obj.__class__):
                object.__setattr__(self, key, value)
                return

        if value == lock_obj:
            object.__setattr__(self, key, value)
            return

        err_msg = 'Cannot set "{}" because it is the incorrect got: {} expects: {}'.format(
            key,
            str(value),
            str(lock_obj)
        )
        raise TypeError(err_msg)


if __name__ == '__main__':

    class Locked(object):
        def __init__(self, thing):
            self.thing = thing


    class Person(TypeBound):
        name = str
        age = int
        gender = str
        hp = type


    class Player(Person):
        def __init__(self, player_dict):
            super(Player, self).__init__()
            for key, value in player_dict.items():
                setattr(self, key, value)


    class Enemy(Player):
        def __init__(self, enemy_dict):
            super(Enemy, self).__init__(enemy_dict)


    class BattleField(TypeBound):
        id = int
        player = Person
        enemy = Enemy


    bf = BattleField()
    bf.id = 9
    # bf.id = 'ham'
    bf.player = Player({'name': 'bob', 'age': 19, 'gender': 'male', 'hp': 150})
    bf.enemy = Enemy({'name': 'blarfrog', 'age': 53, 'gender': 'male', 'hp': 75})
    bf.enemy.hp -= 15
    print(bf.enemy.hp)

