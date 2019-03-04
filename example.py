from time import sleep
from configparser import ConfigParser
from threading import Thread

import praw
from prawcore.exceptions import RequestException, ResponseException

from prawframe.bot import Bot
from prawframe.client import Client
from prawframe.client import run_command_client
from prawframe.output import Msg, PrintQueue
from prawframe.pluginlib import BasePlugin, PluginWorker
from prawframe.schedules import PluginScheduler


# Inherit from BasePlugin to create a new plugin
class MiniDisplay(BasePlugin):
    shorthand = 'minidisplay'   # Shorthand name for the remote python console.
    update_me = 'Hello World'   # Update this value with the remote python console `minidisplay.update_me = 'goodbye'`

    @classmethod
    def mail_notification(cls):
        cls.print_queue.push('<UpdateMe> {}'.format(cls.update_me))
        mail = False
        if not cls.reddit.read_only:
            for msg in cls.reddit.inbox.unread(limit=1):
                mail = True
                break

        if mail:
            # Use the Msg class to customize how the PrintQueue outputs the string.
            cls.print_queue.push(Msg('You have new messages!', start='\n', end='\n\n', stamp=True))
            return
        elif not mail and not cls.reddit.read_only:
            # Unless you don't have special formatting.
            cls.print_queue.push('No new messages')

        cls.print_queue.push('You must log in to check mail status.')
        return

    @classmethod
    def main(cls):
        cls.mail_notification()


class LargerJob(BasePlugin):
    shorthand = 'largejob'
    break_submission = ''

    @classmethod
    def main(cls):
        first_submission = True

        if cls.reddit.read_only:
            _ = 'You must configure your bot to log in before running example with praw code. Running something else...'
            cls.print_queue.push(_)
            del _
            for i in range(1, 500):
                cls.print_queue.push(str(i))
            return

        # Loop through 300 new submissions and keep track of where to stop
        # the next time `main` is called by checking the submission id
        # against the previous runs first submission id.
        for submission in cls.reddit.subreddit('aww').new(limit=300):
            if submission.id == cls.break_submission:
                if not first_submission:
                    cls.break_submission = ''
                break

            # Use the PrintQueue object to push something onto the thread
            # that prints things out.
            cls.print_queue.push(submission.title)

            if first_submission:
                first_submission = False
                cls.break_submission = submission.id

        return


def main():
    config = ConfigParser()
    config.read('.env')

    # Create the thread for the remote python console.  This thread creates a socket
    # client that connects to the server, receives python code, etc.
    command_client_thread = Thread(
        name='Remote Python Shell Thread',      target=run_command_client,
        args=[config['Console']['Host'], int(config['Console']['Port'])]
    )

    # Create reddit instance.
    reddit = praw.Reddit(
        client_id=config['Reddit']['ClientID'], client_secret=config['Reddit']['Secret'],
        username=config['Reddit']['User'], password=config['Reddit']['Password'],
        user_agent=config['Reddit']['UserAgent']
    )

    # Create a list of plugins to give to the PluginWorker
    plugins = [
        LargerJob,
        MiniDisplay
    ]
    # Add plugins to the PluginWorker
    PluginWorker.add_plugins(plugins)

    # To schedule a plugin run the schedule method and give
    # it a minute and the optional hour (default is 1).
    # This will run every if the current hour % 1 == 0
    # and the current minute % 2 == 0.
    LargerJob.schedule(2, hour=1)

    # The bot has an instance of PluginWorker.  PluginWorker loops through a list
    # of plugins and executes their `main()` method.  It also executes scheduled
    # plugins, etc.
    # The reddit instance is automatically attached to the PluginWorker object
    # by the Bot object.  The PluginWorker object automatically attaches any
    # objects the Plugins require (per the framework design) automatically
    # as well (including praw/reddit/config instance).
    Bot.praw = praw
    Bot.reddit = reddit
    Bot.config = config
    Bot.print_queue = PrintQueue
    Bot.plugin_worker = PluginWorker

    # For now the PrintQueue uses another thread so it has to be started
    # using the listen method.
    PrintQueue.listen()

    # The plugin scheduler handles scheduled plugins.  Without it the
    # bot will not run them at their scheduled intervals.
    Bot.plugin_scheduler = PluginScheduler
    Bot.threads = [command_client_thread]

    # Start the remote python shell thread.
    command_client_thread.start()

    # Start up the bot.
    Bot.main()

    # Join threads.
    PrintQueue.join_thread()
    command_client_thread.join()

    # Join scheduler threads.
    if Bot.plugin_scheduler:
        Bot.plugin_scheduler.join_threads()


while True:
    try:
        main()
    except (RequestException, ResponseException) as e:
        PrintQueue.push(Msg('RequestException: {}'.format(e)))

        # Join all threads
        Bot.plugin_scheduler.join_threads()
        PrintQueue.join_thread()
        for thread in Bot.threads:
            thread.join()

        # Wait 10 minutes if there is a network error.
        # Reddit servers may be under heavy load.
        # Give them a break.
        if '404' in '{}'.format(e):
            sleep(600)
        else:
            sleep(600)

        PrintQueue.push(Msg('Rebooting...'))
        continue

    except KeyboardInterrupt:
        # Set events to shut down the socket connection
        Client.restart = True
        Client.shutdown = True

        # Wait for the socket to close any and all connections!
        while Client.alive:
            sleep(0.05)
