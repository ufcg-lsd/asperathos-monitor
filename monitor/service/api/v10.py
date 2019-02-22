# Copyright (c) 2017 UFCG-LSD.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import ConfigParser
import os
import filecmp
import shutil
import sys

from monitor.service import api
from monitor import exceptions as ex
from monitor.utils.logger import Log
from monitor.plugins.builder import MonitorBuilder


API_LOG = Log("APIv10", "APIv10.log")

monitored_apps = {}
builder = MonitorBuilder()


def start_monitoring(data, app_id):
    """ These conditional cases choose the class executor's constructor of the 
    application submitted
    Note: some executors need the keypair to access remotely some machine and
    execute the monitoring logic, but this attribute is not mandatory for all
    the executors."""
 
    if 'plugin' not in data or 'plugin_info' not in data:
        API_LOG.log("Missing parameters in request")
        raise ex.BadRequestException()

    plugin = data['plugin']
    plugin_info = data['plugin_info']
   
    if app_id not in monitored_apps:
        executor = builder.get_monitor(plugin, app_id, plugin_info)
        monitored_apps[app_id] = executor
        executor.start()

    else:
        API_LOG.log("The application is already being monitored")
        raise ex.BadRequestException()


def stop_monitoring(app_id):
    if app_id not in monitored_apps:
        API_LOG.log("App doesn't exist")
        raise ex.BadRequestException()

    # Stop the plugin and remove from the data structure
    monitored_apps.pop(app_id, None).stop()
