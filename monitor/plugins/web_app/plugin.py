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

import paramiko
import time

from monitor.utils.monasca.connector import MonascaConnector
from monitor.plugins.base import Plugin


class WebAppMonitor(Plugin):

    def __init__(self, app_id, info_plugin, keypair, retries=60):
        Plugin.__init__(self, app_id, info_plugin,
                        collect_period=5, retries=retries)
        self.app_id = app_id
        self.host_ip = info_plugin['host_ip']
        self.keypair_path = keypair
        self.host_username = info_plugin['host_username']
        self.log_path = info_plugin['log_path']
        self.dimensions = {'app_id': self.app_id, 'host': self.host_ip}
        self.last_checked = ''
        self.monasca = MonascaConnector()

    def _get_metric_value(self, log):
        value = None
        for i in range(len(log) - 1, 0, -1):
            if log[i] == '#':
                value = float(log[i + 1:-1])
        return value

    def _get_ssh_connection(self):
        keypair = paramiko.RSAKey.from_private_key_file(self.keypair_path)
        conn = paramiko.SSHClient()
        conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        conn.connect(hostname=self.host_ip,
                     username=self.host_username, pkey=keypair)
        return conn

    def _publish_metrics(self, last_log):
        metric = {}
        print(last_log)
        # Check if this log line contains a new metric measurement
        if '[Random]' in last_log and self.last_checked != last_log:
            self.last_checked = last_log
            # Add to metric_info values for this measurement:
            # value and timestamp
            value = self._get_metric_value(last_log)
            metric['name'] = 'web_app.random'
            metric['value'] = value
            metric['timestamp'] = time.time() * 1000
            metric['dimensions'] = {"app_id": self.app_id,
                                    "host": self.host_ip}
            # Sending the metric to Monasca
            print value
            self.monasca.send_metrics([metric])
            print "WebApp metric published: %i" % (value)

        # Flag that checks if the log capture is ended
        elif '[END]' in last_log:
            self.running = False

    def monitoring_application(self):
        try:

            conn = self._get_ssh_connection()
            stdin, stdout, stderr = conn.exec_command("sudo tail -1 %s"
                                                      % self.log_path)
            self._publish_metrics(stdout.read())

        except Exception as ex:
            print "Monitoring %s is not possible. \nError: %s. %s\
                 remaining attempts" % (self.app_id, ex.message, self.attempts)
            raise ex
