try:
    from prawframe.output import Msg
except ImportError:
    from .output import Msg


class BasePlugin(object):
    config = None
    enabled = True
    loading_icon = None
    praw = None
    reddit = None
    wait = False
    disabled = False
    scheduled = False
    hour = 1
    minute = 10
    shorthand = None
    print_queue = None

    @classmethod
    def print(cls):
        excludes = ['__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__gt__', '__hash__', '__init__', '__le__', '__lt__', '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__']
        attrs = [attr for attr in dir(cls) if attr not in excludes]

        output = ''
        for attr in attrs:
            msg = '{} - {}'.format(attr, getattr(cls, attr))
            output += msg + '\n'

        return output

    @classmethod
    def schedule(cls, minute, hour=1):
        cls.hour, cls.minute = hour, minute
        cls.scheduled = True
        return

    @classmethod
    def unschedule(cls):
        cls.scheduled = False
        return

    @classmethod
    def icon_tick(cls):
        cls.loading_icon.tick()
        cls.loading_icon.load()
        return

    @classmethod
    def icon_tick_only(cls):
        cls.loading_icon.tick()
        return

    @classmethod
    def icon_reset_ticks(cls):
        cls.loading_icon.load()
        cls.loading_icon.reset_ticks()
        return

    @classmethod
    def icon_load(cls):
        cls.loading_icon.load()
        return

    @staticmethod
    def main():
        pass


class PluginWorker(object):
    config = None
    praw = None
    reddit = None
    plugins = []
    scheduled = []
    loading_icon = None
    _return_index = None
    running_scheduled = False
    print_queue = None

    @classmethod
    def run_plugin(cls, plugin):
        if hasattr(plugin.__class__, '__name__') and plugin.__class__.__name__ != 'type':
            header_name = plugin.__class__.__name__
        else:
            header_name = plugin.__name__
        header = '{} {} {}'.format('#' * 20, header_name, '#' * 20)

        if not plugin.reddit:
            plugin.reddit = cls.reddit

        if not plugin.loading_icon:
            plugin.loading_icon = cls.loading_icon

        header = Msg(header, stamp=False)
        cls.print_queue.push(header)

        plugin.main()

        footer = Msg('#' * len(Msg(header, stamp=False)), end='\n\n', stamp=False)
        cls.print_queue.push(footer)
        return

    @classmethod
    def add_plugins(cls, plugins):
        cls.plugins += list(plugins)
        return cls.plugins

    @classmethod
    def work(cls):
        disabled_plugins = [plugin for plugin in cls.plugins if plugin.disabled]
        for dplugin in disabled_plugins:
            cls.print_queue.push(Msg('!!!!!!!!!!! {} IS DISABLED !!!!!!!!!!!'.format(dplugin.__name__)))

        cls.print_queue.push(Msg('Executing plugins...', end='\n\n'))
        enabled_plugins = [plugin for plugin in cls.plugins if plugin.enabled and not plugin.disabled]
        enabled_plugins = [plugin for plugin in enabled_plugins if not plugin.scheduled]
        for i, plugin in enumerate(enabled_plugins):

            cls.run_plugin(plugin)

            if len(cls.scheduled) > 0:

                cls.running_scheduled = True
                for scheduled_plugin in cls.scheduled:
                    if scheduled_plugin.disabled or not scheduled_plugin.enabled:
                        continue
                    cls.run_plugin(scheduled_plugin)
                cls.scheduled = []
                cls.running_scheduled = False

        cls.print_queue.push(Msg('Plugin execution completed...', end='\n\n'))
