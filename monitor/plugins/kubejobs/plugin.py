# Copyright (c) 2018 UFCG-LSD.
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

import redis
import requests
import time
import subprocess
from subprocess import PIPE

from datetime import datetime
from monitor.utils.monasca.connector import MonascaConnector
from monitor.plugins.base import Plugin

import kubernetes

LOG_FILE = "progress.log"
TIME_PROGRESS_FILE = "time_progress.log"
MONITORING_INTERVAL = 2


class KubeJobProgress(Plugin):

    def __init__(self, app_id, info_plugin, collect_period=2, retries=10):
        Plugin.__init__(self, app_id, info_plugin,
                        collect_period, retries=retries)

        self.enable_monasca = info_plugin['graphic_metrics']
        if self.enable_monasca:
            self.monasca = MonascaConnector()
        self.submission_url = info_plugin['count_jobs_url']
        # print self.submission_url
        self.expected_time = int(info_plugin['expected_time'])
        self.number_of_jobs = int(info_plugin['number_of_jobs'])
        self.submission_time = datetime.strptime(info_plugin['submission_time'],
                                                 '%Y-%m-%dT%H:%M:%S.%fGMT')
        self.dimensions = {'application_id': self.app_id,
                           'service': 'kubejobs'}
        # print info_plugin['redis_ip'], info_plugin['redis_port']
        self.rds = redis.StrictRedis(host=info_plugin['redis_ip'],
                                     port=info_plugin['redis_port'])
        self.metric_queue = "%s:metrics" % self.app_id
        self.current_job_id = 0

    def _publish_measurement(self, job_request):

        application_progress_error = {}
        job_progress_error = {}
        time_progress_error = {}
        cluster_size = {}
        parallelism = {}

        # Init
        jobs_completed = int(job_request.json())
        print "Jobs Completed: %i" % jobs_completed

        # Job Progress

        job_progress = min(1.0, (float(jobs_completed) / self.number_of_jobs))

        # Elapsed Time
        elapsed_time = float(self._get_elapsed_time())

        # Reference Value
        ref_value = (elapsed_time / self.expected_time)
        replicas = self._get_num_replicas()
        # Error
        print "Job progress: %s\Time Progress: %s\nReplicas: %s" \
                        "\n========================" \
                        % (job_progress, ref_value, replicas)

        error = job_progress - ref_value

        application_progress_error['name'] = ('application-progress'
                                              '.error')

        job_progress_error['name'] = 'job-progress'

        time_progress_error['name'] = 'time-progress'

        application_progress_error['value'] = error
        application_progress_error['timestamp'] = time.time() * 1000
        application_progress_error['dimensions'] = self.dimensions

        job_progress_error['value'] = job_progress
        job_progress_error['timestamp'] = time.time() * 1000
        job_progress_error['dimensions'] = self.dimensions

        time_progress_error['value'] = ref_value
        time_progress_error['timestamp'] = time.time() * 1000
        time_progress_error['dimensions'] = self.dimensions

        cluster_size['name'] = "cluster_size"
        cluster_size['value'] = self._get_cluster_size()
        cluster_size['timestamp'] = time.time() * 1000
        cluster_size['dimensions'] = self.dimensions

        parallelism['name'] = "job-parallelism"
        parallelism['value'] = replicas
        parallelism['timestamp'] = time.time() * 1000
        parallelism['dimensions'] = self.dimensions


        print "Error: %s " % application_progress_error['value']

        self.rds.rpush(self.metric_queue,
                       application_progress_error)

        if self.enable_monasca:
            self.monasca.send_metrics([application_progress_error])
            self.monasca.send_metrics([job_progress_error])
            self.monasca.send_metrics([time_progress_error])
            self.monasca.send_metrics([cluster_size])
            self.monasca.send_metrics([parallelism])


        time.sleep(MONITORING_INTERVAL)

    def _get_cluster_size(self):

        bash_command = 'kubectl get nodes'
        p = subprocess.Popen(bash_command, stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=True)
        o, e = p.communicate()

        
        lines = o.split('\n')
        nodes = {}

        for l in lines:
            if len(l) > 0 and "NAME" not in l:
                nodes[l.split()[0]] = 0

        return len(nodes)-1

    def _get_num_replicas(self):
        kubernetes.config.load_kube_config()

        b_v1 = kubernetes.client.BatchV1Api()

        job = b_v1.read_namespaced_job(name = self.app_id, namespace="default")
        return job.status.active

    def _get_elapsed_time(self):
        datetime_now = datetime.now()
        elapsed_time = datetime_now - self.submission_time
        print "Elapsed Time: %.2f" % elapsed_time.seconds

        return elapsed_time.seconds

    def monitoring_application(self):
        try:
            job_request = requests.get('%s/redis-%s/job:results/count' % (self.submission_url,
                                                                          self.app_id))

            self._publish_measurement(job_request)

        except Exception as ex:
            print ("Error: No application found for %s. %s remaining attempts"
                   % (self.app_id, self.attempts))

            print ex.message
            raise
