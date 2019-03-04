import string as st


def circular_add(start, amount, rng=(30, 126)):
    output = start + amount
    if output > rng[1]:
        output -= rng[1]
        output += rng[0] - 1
        if output > rng[1]:
            output = circular_add(rng[1], output - rng[1], rng=rng)

    return output


def circular_subtract(start, amount, rng=(30, 126)):
    output = start - amount

    if output < rng[0]:
        output += rng[1] + 1
        output -= rng[0]
        if output < rng[0]:
            output = circular_subtract(rng[0], rng[0] - output, rng=rng)

    return output


class Dial(object):
    def __init__(self, start, rng=(30, 126)):
        self.start = start
        self.rng = rng
        self.full_rng = rng[1] - rng[0]
        self.rng_list = list(range(rng[0], rng[1] + 1))
        self.pointer = self.rng_list.index(start)
        self.current = self.rng_list[self.pointer]

    def _increment(self):
        if self.pointer == len(self.rng_list) - 1:
            self.pointer = 0
            self.current = self.rng_list[self.pointer]
            return True
        self.pointer += 1
        self.current = self.rng_list[self.pointer]
        return True

    def _decrement(self):
        if self.pointer == 0:
            self.pointer = len(self.rng_list) - 1
            self.current = self.rng_list[self.pointer]
            return True

        self.pointer -= 1
        self.current = self.rng_list[self.pointer]
        return True

    def set_pointer(self, point):
        self.pointer = self.rng_list.index(point)
        self.current = self.rng_list[self.pointer]
        return self

    def add(self, amount):
        while amount > self.rng[1]:
            amount = amount // self.full_rng + amount % self.full_rng

        for i in range(amount):
            self._increment()

        return self.current

    def sub(self, amount):
        # Reduce the amount of iterations we need to perform.
        while amount > self.rng[1]:
            amount = amount // self.full_rng + amount % self.full_rng

        for i in range(amount):
            self._decrement()

        return self.current


class Scrambler(object):
    # characters = [c for c in st.ascii_letters + "1234567890-=`~!@#$%^&*()_+\\][|{}';/.,\":?>< "]
    characters = [c for c in st.printable]
    rev_ord = {ord(c): c for c in characters}
    ord = {c: ord(c) for c in characters}

    def __init__(self):
        Scrambler.rev_ord[31] = '\n'
        Scrambler.ord['\n'] = 31

        Scrambler.rev_ord[30] = '\t'
        Scrambler.ord['\t'] = 30

    def scramble(self, string):
        if not string:
            # raise ValueError("String cannot be empty.")
            return string

        first_letter_ord = Scrambler.ord[string[0]]
        output = ""

        for i, c in enumerate(string):
            d1 = Dial(Scrambler.ord[c])
            c_ord = d1.add(sum([Scrambler.ord[x] for x in string[:i]]))
            if i == 0:
                out = c
            else:
                d1.set_pointer(first_letter_ord)
                _ = d1.add(c_ord)
                out = Scrambler.rev_ord[_]

            output += out
            first_letter_ord = Scrambler.ord[c]

        d1.set_pointer(Scrambler.ord[string[0]])
        first_letter_number = d1.add(sum([Scrambler.ord[x] for x in output[1:]]))
        output = Scrambler.rev_ord[first_letter_number] + output[1:]
        return output

    def unscramble(self, string):
        if not string:
            # raise ValueError("String cannot be empty.")
            return string

        first_letter_ord = Scrambler.ord[string[0]]
        if not first_letter_ord:
            raise ValueError("Your message is invalid.")

        output = ""

        # Set string's first letter to the correct un-encoded letter.
        d1 = Dial(first_letter_ord)
        first_letter_number = d1.sub(sum([Scrambler.ord[x] for x in string[1:]]))
        first_letter = Scrambler.rev_ord[first_letter_number]
        string = first_letter + string[1:]

        for i, c in enumerate(string):
            d1.set_pointer(Scrambler.ord[c])
            c_ord = d1.sub(sum([Scrambler.ord[x] for x in output[:i]]))
            if i == 0:
                out = c
            else:
                last_c_ord = Scrambler.ord[output[-1]]
                d1.set_pointer(c_ord)
                out_ord = d1.sub(last_c_ord)
                out = Scrambler.rev_ord[out_ord]

            output += out
            first_letter_ord = Scrambler.ord[out]

        return output


if __name__ == '__main__':
    print(''.join(Scrambler.characters))
    s = Scrambler()
    o = """ScrambledEggs is a text encoding / obfuscation tool that was created
for fun.

It turns text into something like this:"""

    print('\nstring:', o)
    o = s.scramble(o)
    print('\nencoded:', o)
    o = s.unscramble(o)
    print('\ndecoded:', o)
