from threading import Thread
from time import sleep


name = 'prawframe'


class Text(object):
    string = 'hello'

    def __init__(self, string):
        self.string = string

    @classmethod
    def p(cls):
        print(cls.string)


l = []
for i in range(500):
    l.append(Text(str(i)))


Text.p()


class Queue(object):
    data = []


class Robot(object):
    queue = Queue

    def __init__(self, queue=None):
        self.queue = queue if queue else Queue

    @classmethod
    def scrape(cls, url):
        """
        This is a "fake" method that does nothing except add a string to a queue.

        :param url:
        :return:
        """
        cls.queue.data.append(url)
        return


class DownloadLimiter(object):
    queue = Queue
    enabled = True
    _started = False

    def __init__(self, queue=None):
        self.queue = queue if queue else Queue

    @classmethod
    def main(cls):
        """
        Run this method in a new thread.  It pops items off the front of a queue and prints them
        while limiting how quickly it does it.  Calling the shutdown method will shut down ALL
        instances of DownloadLimiter (each instance stopping as soon as
        :return:
        """
        while DownloadLimiter.enabled:  # Keep things running until `shutdown` is called.
            while cls.queue.data:   # Process queue items.
                # It's possible that someone could call the shutdown method before there is queue data
                # so _started is used to make sure there has been data in the queue
                cls._started = True
                try:
                    item = cls.queue.data.pop(0)
                except IndexError:
                    continue
                print(item)
                sleep(2)
                # do stuff to scrape new url from html returned from original url or something
        return

    @classmethod
    def _safe_stop_wait(cls):
        """
        If nothing has been processed in the queue then don't shut down.

        :return:
        """
        while not cls._started:
            sleep(.1)
            continue
        return

    @classmethod
    def shutdown(cls, all_instances=False):
        """
        Set the `enabled` attribute to False.  DownloadLimiter will finish processing items in the queue
        and then shut down.

        :param all_instances:
        :return:
        """
        cls._safe_stop_wait()
        if all_instances:
            DownloadLimiter.enabled = False
            return cls
        cls.enabled = False
        return cls


queue1 = Queue()
queue2 = Queue()

limiter1 = DownloadLimiter(queue=queue1)
limiter2 = DownloadLimiter(queue=queue2)

r1 = Robot(queue=queue1)
r2 = Robot(queue=queue2)

for i in range(5):
    r1.scrape('https://google.com/{}'.format(i + 1))
    r2.scrape('https://bing.com/{}'.format(i + 1))

t1 = Thread(target=limiter1.main)
t2 = Thread(target=limiter2.main)

t1.start()
t2.start()

limiter1.shutdown(all_instances=True)

t1.join()
t2.join()
