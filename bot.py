from time import sleep
try:
    from prawframe.common import StaticLoadingIcon
    from prawframe.output import Msg
except ImportError:
    from .common import StaticLoadingIcon
    from .output import Msg


class Bot(object):
    config = None
    client = None
    praw = None
    reddit = None
    debug_mode = False
    plugin_worker = None
    on_main = []
    plugin_scheduler = None
    threads = []
    loading_icon = StaticLoadingIcon
    print_queue = None

    @classmethod
    def _vefify_attributes(cls):
        attrs = [
            'config', 'praw', 'reddit', 'plugin_worker', 'loading_icon', 'print_queue', 'client'
        ]

        for attr in attrs:
            if getattr(cls, attr) is None:
                err = 'Bot.{} must be set before bot can function.'.format(attr)
                raise ValueError(err)

    @classmethod
    def bootstrap_plugins(cls):
        for plugin in cls.plugin_worker.plugins:
            plugin.reddit = cls.reddit
            if not plugin.loading_icon:
                plugin.loading_icon = cls.loading_icon
            if not plugin.print_queue:
                plugin.print_queue = cls.print_queue
            if not plugin.praw:
                plugin.praw = cls.praw
            if not plugin.config:
                plugin.config = cls.config
        return

    @classmethod
    def bootstrap_plugin_worker(cls):
        if not cls.plugin_worker.reddit:
            cls.plugin_worker.reddit = cls.reddit
        if not cls.plugin_worker.loading_icon:
            cls.plugin_worker.loading_icon = cls.loading_icon
        if not cls.plugin_worker.print_queue:
            cls.plugin_worker.print_queue = cls.print_queue
        if not cls.plugin_worker.praw:
            cls.plugin_worker.praw = cls.praw
        if not cls.plugin_worker.config:
            cls.plugin_worker.config = cls.config
        return

    @classmethod
    def bootstrap_plugin_scheduler(cls):
        if not cls.plugin_scheduler:
            return
        if not cls.plugin_scheduler.loading_icon:
            cls.plugin_scheduler.loading_icon = cls.loading_icon
        if not cls.plugin_scheduler.print_queue:
            cls.plugin_scheduler.print_queue = cls.print_queue
        if not cls.plugin_scheduler.config:
            cls.plugin_scheduler.config = cls.config
        return

    @classmethod
    def main(cls):
        cls._vefify_attributes()

        # Bootstrap objects - Set attributes to relevant objects.
        if cls.client and not cls.client.bot:
            cls.client.bot = cls
        cls.bootstrap_plugins()
        cls.bootstrap_plugin_worker()
        cls.bootstrap_plugin_scheduler()

        # Run on_main callbacks
        for on_inst_plugin in cls.on_main:
            if not on_inst_plugin.reddit:
                on_inst_plugin.reddit = cls.reddit
            on_inst_plugin.main()

        # Handle the plugin scheduler.
        if cls.plugin_scheduler:
            cls.plugin_scheduler.plugin_worker = cls.plugin_worker
            cls.plugin_scheduler.plugins = cls.plugin_worker.plugins
            cls.plugin_scheduler.create_threads()
            cls.plugin_scheduler.start_threads()

        wait_time = int(cls.config['Misc']['WaitTime'])
        # Run the main loop
        while True:
            # Cycle through plugins and run the `main` method on each plugin.
            cls.plugin_worker.work()

            sleep_seconds = wait_time

            message = Msg('Sleeping for {} seconds...'.format(sleep_seconds), end='\n\n')
            cls.print_queue.push(message)

            sleep_timer = sleep_seconds
            while sleep_timer > 0:
                sleep(1)
                sleep_timer -= 1
                StaticLoadingIcon.tick()
                StaticLoadingIcon.load(end=str(sleep_timer).zfill(3))

            StaticLoadingIcon.reset_ticks()
