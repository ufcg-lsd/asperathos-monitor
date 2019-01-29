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

import unittest
import requests_mock
import pytest

from monitor.tests.unit.mocks.mock_redis import MockRedis
from monitor.tests.unit.mocks.mock_k8s import MockKube
from monitor.tests.unit.mocks.mock_monasca import MockMonascaConnector
from datetime import datetime


from monitor.plugins.kubejobs.plugin import KubeJobProgress

"""
Class that tests the KubeJobsPlugin components.
"""
class TestKubeJobs(unittest.TestCase):

    """
    Set up variables that KubeJobs plugin needs
    """    
    def setUp(self):

        self.app_id = "kj-10111213"
        self.info_plugin = {
            "monitor_plugin": "kubejobs",
            "graphic_metrics": False,
            "expected_time": 500,
            "count_jobs_url": "mock.com",
            "number_of_jobs": 1500,
            "submission_time": "2017-04-11T00:00:00.0003GMT",
            "redis_ip": "192.168.0.0",
            "redis_port": 5000, 
            "enable_visualizer": True,
            "datasource_type": "influxdb",
            "database_data": {
                "name": "influxdb",
                "url": "url.com",
                "port": "0000"
            }
        }

        self.collect_period = 5
        self.retries = 20

    def tearDown(self):
        pass

    """
    Test the KubeJobs Plugin constructor, checking if the
    plugin's attributes are equals that atributes given
    """
    def test_init_kubejobs(self):

        plugin = KubeJobProgress(self.app_id, self.info_plugin,
                                 self.collect_period, self.retries)

        self.assertEqual(plugin.app_id, self.app_id)
        self.assertEqual(plugin.info_plugin, self.info_plugin)
        self.assertEqual(plugin.collect_period, self.collect_period)
        self.assertEqual(plugin.attempts, self.retries)

        plugin2 = KubeJobProgress(self.app_id, self.info_plugin)

        self.assertEqual(plugin2.app_id, self.app_id)
        self.assertEqual(plugin2.info_plugin, self.info_plugin)
        self.assertEqual(plugin2.collect_period, 2)
        self.assertEqual(plugin2.attempts, 10)

        self.assertFalse(plugin == plugin2)


    """
    Verify that the number of replicas returned are equal
    that number of replicas initial
    """    
    def test_get_num_replicas(self):

        plugin = KubeJobProgress(self.app_id, self.info_plugin,
                                 self.collect_period, self.retries)

        plugin.b_v1 = MockKube(plugin.app_id)
        self.assertEqual(plugin._get_num_replicas(), 1)

        plugin.b_v1 = MockKube(plugin.app_id, 3)
        self.assertEqual(plugin._get_num_replicas(), 3)

    """
    Verify that when a measurement is pubished, the
    metrics are delivered to Redis queue
    """
    @pytest.mark.skip(reason="Obsolete test")
    def test_publish_measurement(self):

        plugin = KubeJobProgress(self.app_id, self.info_plugin,
                                 self.collect_period, self.retries)

        plugin.rds = MockRedis()
        plugin.b_v1 = MockKube(plugin.app_id)

        plugin._publish_measurement(500)
        self.assertTrue(plugin.rds.rpop(plugin.metric_queue) != None)
        self.assertTrue(plugin.rds.rpop(plugin.metric_queue) == None)
        
        plugin._publish_measurement(600)
        self.assertTrue(plugin.rds.rpop(plugin.metric_queue) != None)
        self.assertTrue(plugin.rds.rpop(plugin.metric_queue) == None)

    """
    Check that the elapsed time returned (in seconds) 
    is equal that elapsed time given
    """
    def test_get_elapsed_time(self):

        plugin = KubeJobProgress(self.app_id, self.info_plugin,
                                 self.collect_period, self.retries)

        datetime_now = datetime.now()
        elapsed_time = datetime_now - plugin.submission_time
                        
        self.assertEqual(elapsed_time.seconds, plugin._get_elapsed_time())

    """
    Check that the function monitoring_application 
    returns the number of jobs minus the number of
    jobs that are be processing plus number of jobs to do 
    """
    @pytest.mark.skip(reason="Obsolete test")
    def test_monitoring_application(self):
        
        plugin = KubeJobProgress(self.app_id, self.info_plugin,
                                 self.collect_period, self.retries)
        plugin.rds = MockRedis()
        plugin.b_v1 = MockKube(plugin.app_id)

        with requests_mock.Mocker() as m:

            m.get('http://%s/redis-%s/job/count' % (plugin.submission_url,
                                             plugin.app_id), text='500')

            m.get('http://%s/redis-%s/job:processing/count' % (plugin.submission_url,
                                             plugin.app_id), text='750')

            self.assertEqual(plugin.monitoring_application(), 250)

    """
    Verify that when the flag enable_monasca is True,
    the metrics are delivered to Monasca
    """
    @pytest.mark.skip(reason="Obsolete test")
    def test_send_monasca_metrics(self):

        plugin = KubeJobProgress(self.app_id, self.info_plugin,
                                 self.collect_period, self.retries)

        plugin.rds = MockRedis()
        plugin.b_v1 = MockKube(plugin.app_id)
        plugin.monasca = MockMonascaConnector()
        plugin.enable_monasca = True

        plugin._publish_measurement(5000)

        self.assertEqual(len(plugin.monasca.metrics['time-progress']), 1)
        self.assertEqual(len(plugin.monasca.metrics['job-progress']), 1)
        self.assertEqual(len(plugin.monasca.metrics['application-progress.error']), 1)
        self.assertEqual(len(plugin.monasca.metrics['job-parallelism']), 1)

        plugin._publish_measurement(1000)

        self.assertEqual(len(plugin.monasca.metrics['time-progress']), 2)
        self.assertEqual(len(plugin.monasca.metrics['job-progress']), 2)
        self.assertEqual(len(plugin.monasca.metrics['application-progress.error']), 2)
        self.assertEqual(len(plugin.monasca.metrics['job-parallelism']), 2)


if __name__ == "__main__":
    unittest.main()
