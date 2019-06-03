import subprocess
from importlib import import_module
from monitor.utils import logger

API_LOG = logger.Log('api', 'api.log')


class PluginSources(object):
    GIT = 'git'
    PIP = 'pip'


def install_plugin(source, plugin):
    if source == PluginSources.GIT:
        install_name = 'git+' + plugin
    elif source == PluginSources.PIP:
        install_name = plugin
    try:
        exit_status = subprocess.check_call(['pip',
                                             'install',
                                             '--upgrade',
                                             install_name])
    except Exception as e:
        API_LOG.log(e)
        return False
    return exit_status == 0


def get_plugin(plugin_module):
    plugin = import_module(plugin_module).PLUGIN
    return plugin
