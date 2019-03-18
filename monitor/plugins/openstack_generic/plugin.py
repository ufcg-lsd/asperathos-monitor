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


class OSGeneric(Plugin):
    def __init__(self, app_id, info_plugin, keypair, retries=60):
        Plugin.__init__(self, app_id, info_plugin, collect_period=5,
                        retries=retries)

        self.app_id = app_id
        self.host_ip = info_plugin['host_ip']
        self.expected_time = info_plugin['expected_time']
        self.log_path = info_plugin['log_path']
        self.keypair_path = keypair
        self.host_username = 'ubuntu'
        self.dimensions = {"application_id": self.app_id,
                           "host": self.host_ip}

        self.last_checked = ''
        self.start_time = time.time()
        self.monasca = MonascaConnector()

    """ This method extracts the value information from a log line
        that contains the measurement for the interest metric """

    def _get_metric_value(self, log):
        value = None
        for i in range(len(log) - 1, 0, -1):
            if log[i] == '#':
                value = float(log[i + 1:-1])

        return value

    def _get_elapsed_time(self):
        delay = time.time() - self.start_time
        return delay

    """ This method returns a remote connection with the host where
        the log will be captured. It is possible to execute a command
        in the host using the function c.exec_command("write_command_here")
        with the object returned here """

    def _get_ssh_connection(self):
        keypair = paramiko.RSAKey.from_private_key_file(self.keypair_path)
        conn = paramiko.SSHClient()
        conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        conn.connect(hostname=self.host_ip, username=self.host_username,
                     pkey=keypair)

        return conn

    """ This is an auxiliary function to prepare and publish the metric.
        The point is to keep monitoring_application as simple as possible. """

    def _publish_metrics(self, last_log):
        metric = {}
        print last_log

        # Check if this log line contains a new metric measurement.
        if '[Progress]' in last_log and self.last_checked != last_log:
            self.last_checked = last_log

            """ Add to metric_info values for this measurement:
                value and timestamp """
            ref_value = self._get_elapsed_time() / self.expected_time
            measurement_value = self._get_metric_value(last_log)
            error = measurement_value - ref_value

            """ The Monasca metric must have the 3 following fields to be
                created: name, value and timestamp, but also is possible to
                increment the metrics identities - using dimensions -  and
                informations - using value_meta, a dictionary that contains
                aditional information about the measurement. """

            metric['name'] = 'application-progress.error'
            metric['value'] = error
            metric['timestamp'] = time.time() * 1000
            metric['dimensions'] = self.dimensions

            time_progress_metric = {}
            time_progress_metric['name'] = 'application-progress.time_progress'
            time_progress_metric['value'] = ref_value
            time_progress_metric['timestamp'] = time.time() * 1000
            time_progress_metric['dimensions'] = self.dimensions

            app_progress_metric = {}
            app_progress_metric['name'] = 'application-progress.app_progress'
            app_progress_metric['value'] = measurement_value
            app_progress_metric['timestamp'] = time.time() * 1000
            app_progress_metric['dimensions'] = self.dimensions

            # Sending the metric to Monasca
            self.monasca.send_metrics([metric, app_progress_metric,
                                       time_progress_metric])

            print "Application progress error: %.4f" % error

        # Flag that checks if the log capture is ended
        elif '[END]' in last_log:
            self.running = False

    def monitoring_application(self):
        try:
            # First of all, a connection with the host is created.
            conn = self._get_ssh_connection()

            """ The second step consists in execute the command to capture
                the last log line from the log file using the connection
                create below and saving the outputs. """
            stdin, stdout, stderr = conn.exec_command(
                "sudo tail -1 %s" % self.log_path)

            # The last step is to actually publish using the captured log line
            self._publish_metrics(stdout.read())

        except Exception as ex:
            print "Monitoring %s is not possible. \n\
                   Error: %s. %s remaining attempts" % (self.app_id,
                                                        ex.message,
                                                        self.attempts)

            raise ex
