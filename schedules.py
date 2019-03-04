from threading import Thread
from time import sleep
from datetime import datetime
try:
    from prawframe.output import PrintQueue
except ImportError:
    from .output import PrintQueue


def minute_schedule(m, mins=10):
    a = int(60 / mins)
    low = 0
    high = low + 5
    out = []
    for i in range(a):
        out.append((m >= low and m <= high))
        low += mins
        high = low + 5
    return out


def schedule_plugin(plugin, plugin_worker):
    PrintQueue.push('Starting plugin controller: {}'.format(plugin.__name__))
    if plugin.disabled:
        PrintQueue.push('!!!!!!!!!!! {} IS DISABLED !!!!!!!!!!!'.format(plugin.__name__))
    last_run = (1000, 1000)
    while True:
        n = datetime.now()
        h, m = n.hour, n.minute
        current_run = (h, m)

        if h % plugin.hour == 0 and m % plugin.minute == 0 and current_run != last_run:
            # If scheduled plugins are running we can't change the size of the list.
            while plugin_worker.running_scheduled:
                sleep(1)

            if plugin not in plugin_worker.scheduled:
                plugin_worker.scheduled.append(plugin)

            last_run = (h, m)
        last_run = (h, m)
        sleep(1)


class PluginScheduler(object):
    config = None
    plugin_worker = None
    plugins = []
    thread_pool = []
    loading_icon = None
    print_queue = None

    @classmethod
    def create_threads(cls):
        for thread in cls.thread_pool:
            thread.join()
        cls.thread_pool = []
        scheduled_plugins = [p for p in cls.plugins if p.scheduled]
        for plugin in scheduled_plugins:
            thread = Thread(
                name='{}'.format(plugin.__class__),
                target=schedule_plugin,
                args=[plugin, cls.plugin_worker],
            )
            cls.thread_pool.append(thread)

    @classmethod
    def start_threads(cls):
        for thread in cls.thread_pool:
            thread.start()
        return

    @classmethod
    def join_threads(cls):
        for thread in cls.thread_pool:
            thread.join()
        return


