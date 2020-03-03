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

import threading
import time

from monitor.utils.logger import Log


LOG_FILE = "base.log"
LOG_NAME = "plugin-base"


# Plugins must extend Thread to facilitate each parallel plugin execution
class Plugin(threading.Thread):

    def __init__(self, app_id, info_plugin, collect_period, retries=30):
        threading.Thread.__init__(self)

        # Contains all the specific information for each plugin
        self.info_plugin = info_plugin

        # Flag that enable or disable the monitoring logic execution
        self.running = False
        self.LOG = Log(LOG_NAME, LOG_FILE)
        # Dimensions is composed by default only application_id, but for each
        # plugin it can change and it is possible to add some relevant
        # information
        self.dimensions = {'application_id': app_id}

        # Time interval between each metric collect
        self.collect_period = collect_period

        # How many times monitoring_application must be re executed when
        # something break into the execution
        self.attempts = retries

        # The identifier for the submitted application
        self.app_id = app_id

    def stop(self):
        print("The {} is stopping for {}...".format(type(self).__name__,
                                                    self.app_id))
        self.running = False

    # This method must be subscribed by each plugin that
    # extends this base class
    def monitoring_application(self):
        pass

    def run(self):
        self.running = True
        while self.running:
            if self.attempts == 0:
                self.stop()
                break
            try:
                time.sleep(self.collect_period)
                self.monitoring_application()

            except Exception as ex:
                self.attempts -= 1
                self.LOG.log(ex)
                time.sleep(self.collect_period)
