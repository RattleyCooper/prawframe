from PyCharmSync import ProjectSync
from configparser import ConfigParser


config = ConfigParser()
config.read('.remote')

ProjectSync.config = config
ProjectSync.main()
