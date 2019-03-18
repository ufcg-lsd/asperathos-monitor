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

import time
from datetime import datetime

import pytz
import requests
import tzlocal
from monitor.utils.monasca.connector import MonascaConnector
from monitor.plugins.base import Plugin
from monitor.utils.logger import Log, configure_logging


LOG_FILE = "progress.log"
TIME_PROGRESS_FILE = "time_progress.log"
MONITORING_INTERVAL = 1

plugin_log = Log("Spark_Progress", "monitor.log")
configure_logging()


class SparkProgress(Plugin):

    def __init__(self, app_id, info_plugin, collect_period=2,
                 retries=60, monasca_conn="monasca"):
        Plugin.__init__(self, app_id, info_plugin,
                        collect_period, retries=retries)

        if monasca_conn == "monasca":
            self.monasca = MonascaConnector()
        else:
            self.monasca = monasca_conn

        self.submission_url = info_plugin['spark_submisson_url']
        self.expected_time = info_plugin['expected_time']

        self.number_of_jobs = int(info_plugin['number_of_jobs'])
        self.job_expected_time = (float(self.expected_time)
                                  / float(self.number_of_jobs))

        self.remaining_time = float(self.expected_time)
        self.current_job_id = 0

        self.app_id = app_id
        self.dimensions = {'application_id': self.app_id,
                           'service': 'spark-sahara'}

        self.job_ratio = 1.0 / self.number_of_jobs
        self.first_submission_time = None

    def _publish_measurement(self, job_request):

        total_time_progress_metric = {}
        total_app_progress_metric = {}
        progress_error_metric = {}

        # Init
        jobs = job_request.json()
        jobs.reverse()

        if not len(jobs) == 0:
            if self.current_job_id == 0:
                self.first_submission_time = \
                    jobs[self.current_job_id]['submissionTime']

            current_job = jobs[self.current_job_id]

            if current_job['status'] == 'FAILED':
                self.current_job_id = len(jobs) - 1

            elif current_job['status'] == 'SUCCEEDED':
                elapsed_time = float(self._get_elapsed_time(
                    current_job['submissionTime']))

                self.remaining_time = self.remaining_time - elapsed_time

                self.current_job_id = len(jobs) - 1

                # Job Time
                if self.remaining_time <= 0.0:
                    self.job_expected_time = -1
                else:
                    self.job_expected_time = (self.remaining_time
                                              / (float(self.number_of_jobs)
                                                 - float(self.current_job_id)))

            elif current_job['status'] == 'RUNNING':
                # Job Progress
                job_progress = (current_job['numCompletedTasks']
                                / float(current_job['numTasks']))

                # Total Elapsed Time
                total_elapsed_time = float(self._get_elapsed_time(
                    self.first_submission_time))

                # Total Time Progress
                total_time_progress = float(
                    total_elapsed_time / self.expected_time)

                # Total Application Progress
                total_app_progress = self.job_ratio * (self.current_job_id
                                                       + job_progress)

                # New Progress Error
                new_progress_error = total_app_progress - total_time_progress

                # Elapsed Time
                elapsed_time = float(self._get_elapsed_time(
                    current_job['submissionTime']))

                plugin_log.log("%s | %s: Elapsed time: %.2f -\
                                         Expected time: %.2f" %
                               (time.strftime("%H:%M:%S"),
                                self.app_id,
                                elapsed_time,
                                self.job_expected_time))

                # Error
                if self.job_expected_time == -1:
                    time_progress = 1
                else:
                    time_progress = (elapsed_time / self.job_expected_time)

                    if time_progress > 1:
                        time_progress = 1

                    job_progress - time_progress

                progress_error_metric = self._format_metric(
                    'application-progress.error',
                    new_progress_error,
                    time.time() * 1000,
                    self.dimensions
                )

                total_app_progress_metric = self._format_metric(
                    'application-progress.total_app_progress',
                    total_app_progress * 100,
                    time.time() * 1000,
                    self.dimensions
                )

                total_time_progress_metric = self._format_metric(
                    'application-progress.total_time_progress',
                    total_time_progress * 100,
                    time.time() * 1000,
                    self.dimensions
                )

                log_string = ("%s | %s: Ref value: %.2f - Job progress: %.2f" %
                              (time.strftime("%H:%M:%S"),
                               self.app_id,
                               time_progress,
                               job_progress))

                plugin_log.log(log_string)

                log_string = ("%s | %s: Job: %d - Progress error: %.2f" %
                              (time.strftime("%H:%M:%S"),
                               self.app_id,
                               self.current_job_id,
                               float(progress_error_metric['value'])))

                plugin_log.log(log_string)

                self.monasca.send_metrics([progress_error_metric,
                                           total_time_progress_metric,
                                           total_app_progress_metric])

            time.sleep(MONITORING_INTERVAL)

    def _format_metric(self, name, value, timestamp, dimensions):
        metric = {}
        metric['name'] = name
        metric['value'] = value
        metric['timestamp'] = timestamp
        metric['dimensions'] = dimensions

        return metric

    def _get_elapsed_time(self, gmt_timestamp):
        local_tz = tzlocal.get_localzone()

        submission_date = datetime.strptime(gmt_timestamp,
                                            '%Y-%m-%dT%H:%M:%S.%fGMT')

        submission_date = submission_date.replace(tzinfo=pytz.utc).\
            astimezone(local_tz)

        submission_date = submission_date.replace(tzinfo=None)

        submission_timestamp = time.mktime(submission_date.timetuple())
        this_timestamp = time.time()

        plugin_log.log("%s | %s: Submission timestamp: %.2f - \
                                 This timestamp: %.2f" %
                       (time.strftime("%H:%M:%S"),
                        self.app_id,
                        submission_timestamp,
                        this_timestamp))

        elapsed_time = this_timestamp - submission_timestamp

        return elapsed_time

    def monitoring_application(self):
        try:
            job_request = requests.get(self.submission_url
                                       + ':4040/api/v1/applications/'
                                       + self.app_id + '/jobs')

            self._publish_measurement(job_request)

        except Exception as ex:
            print ("Error: No application found for %s. %s remaining attempts"
                   % (self.app_id, self.attempts))

            print ex.message
            raise
