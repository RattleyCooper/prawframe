try:
    from prawframe.obfuscation import Scrambler
except ImportError:
    from .obfuscation import Scrambler


def scrambles_input_unscrambles_output(func):
    scrambler = Scrambler()

    def decorator(*args, **kwargs):
        args = list(args)
        args[0] = scrambler.scramble(args[0])
        result = func(*args, **kwargs)
        descrabled = scrambler.unscramble(result)
        return descrabled
    return decorator


def unscrambles_output(func):
    scrambler = Scrambler()

    def decorator(*args, **kwargs):
        args = list(args)
        scrambled_result = func(*args, **kwargs)
        result = scrambler.unscramble(scrambled_result)
        return result
    return decorator


def scrambles_input(func):
    scrambler = Scrambler()

    def decorator(*args, **kwargs):
        args = list(args)
        args[0] = scrambler.scramble(args[0])
        result = func(*args, **kwargs)
        return result
    return decorator
