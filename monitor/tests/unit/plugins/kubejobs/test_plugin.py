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

from datetime import datetime
from mock import patch
import unittest


from monitor import exceptions as ex
from monitor.plugins.kubejobs.plugin import KubeJobProgress
from monitor.tests.mocks.mock_influx import MockInfluxConnector
from monitor.tests.mocks.mock_k8s import MockKube
from monitor.tests.mocks.mock_monasca import MockMonascaConnector
from monitor.tests.mocks.mock_redis import MockRedis


class TestKubeJobs(unittest.TestCase):

    def setUp(self):
        """
        Set up variables that KubeJobs plugin needs
        Args: None
        Returns: None
        """
        self.app_id = "kj-10111213"
        self.info_plugin = {
            "expected_time": 500,
            "number_of_jobs": 1500,
            "submission_time": "2017-04-11T00:00:00.0003GMT",
            "redis_ip": "192.168.0.0",
            "redis_port": 5000,
            "enable_visualizer": True,
            "datasource_type": "influxfb"
        }

        self.collect_period = 5
        self.retries = 20

    def tearDown(self):
        pass

    @patch('kubernetes.config.load_kube_config')
    def test_init_kubejobs(self, mock_config):
        """
        Test the KubeJobs Plugin constructor, checking if the
        plugin's attributes are equals that atributes given
        Args: (patch) -- Path of the Mock of Kubernetes config
        Returns: None
        """
        mock_config.return_value = None

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

    @patch('kubernetes.config.load_kube_config')
    def test_get_num_replicas(self, mock_config):
        """
        Verify that the number of replicas returned are equal
        that number of replicas initial
        Args: (patch) -- Path of the Mock of Kubernetes config
        Returns: None
        """
        mock_config.return_value = None

        plugin = KubeJobProgress(self.app_id, self.info_plugin,
                                 self.collect_period, self.retries)

        plugin.b_v1 = MockKube(plugin.app_id)
        self.assertEqual(plugin._get_num_replicas(), 1)

        plugin.b_v1 = MockKube(plugin.app_id, 3)
        self.assertEqual(plugin._get_num_replicas(), 3)

    @patch('kubernetes.config.load_kube_config')
    def test_publish_measurement(self, mock_config):
        """
        Verify that when a measurement is pubished, the
        metrics are delivered to Redis queue
        Args: (patch) -- Path of the Mock of Kubernetes config
        Returns: None
        """
        mock_config.return_value = None

        plugin = KubeJobProgress(self.app_id, self.info_plugin,
                                 self.collect_period, self.retries)

        plugin.rds = MockRedis()
        plugin.b_v1 = MockKube(plugin.app_id)
        plugin.datasource = MockInfluxConnector()

        plugin._publish_measurement(500)
        self.assertTrue(plugin.rds.rpop(plugin.metric_queue) is not None)
        self.assertTrue(plugin.rds.rpop(plugin.metric_queue) is None)

        plugin._publish_measurement(600)
        self.assertTrue(plugin.rds.rpop(plugin.metric_queue) is not None)
        self.assertTrue(plugin.rds.rpop(plugin.metric_queue) is None)

    @patch('kubernetes.config.load_kube_config')
    def test_get_elapsed_time(self, mock_config):
        """
        Check that the elapsed time returned (in seconds)
        is equal that elapsed time given
        Args: (patch) -- Path of the Mock of Kubernetes config
        Returns: None
        """
        mock_config.return_value = None

        plugin = KubeJobProgress(self.app_id, self.info_plugin,
                                 self.collect_period, self.retries)

        datetime_now = datetime.now()
        elapsed_time = datetime_now - plugin.submission_time

        self.assertEqual(elapsed_time.seconds, plugin._get_elapsed_time())

    @patch('kubernetes.config.load_kube_config')
    def test_monitoring_application(self, mock_config):
        """
        Check that the function monitoring_application
        returns the number of jobs minus the number of
        jobs that are be processing plus number of jobs to do
        Args: (patch) -- Path of the Mock of Kubernetes config
        Returns: None
        """
        mock_config.return_value = None

        plugin = KubeJobProgress(self.app_id, self.info_plugin,
                                 self.collect_period, self.retries)
        plugin.rds = MockRedis()
        plugin.b_v1 = MockKube(plugin.app_id)
        plugin.datasource = MockInfluxConnector()

        for i in range(5):
            plugin.rds.rpush('job', 'job')

        for i in range(10):
            plugin.rds.rpush('job:processing', 'job')

        self.assertEqual(plugin.monitoring_application(), 1485)

    @patch('kubernetes.config.load_kube_config')
    def test_send_monasca_metrics(self, mock_config):
        """
        Verify that when the flag enable_monasca is True,
        the metrics are delivered to Monasca
        Args: (patch) -- Path of the Mock of Kubernetes config
        Returns: None
        """
        mock_config.return_value = None

        plugin = KubeJobProgress(self.app_id, self.info_plugin,
                                 self.collect_period, self.retries)

        plugin.rds = MockRedis()
        plugin.b_v1 = MockKube(plugin.app_id)
        plugin.datasource = MockMonascaConnector()

        plugin._publish_measurement(5000)

        self.assertEqual(len(plugin.datasource.metrics['time-progress']), 1)
        self.assertEqual(len(plugin.datasource.metrics['job-progress']), 1)
        self.assertEqual(
            len(plugin.datasource.metrics['application-progress.error']), 1)
        self.assertEqual(len(plugin.datasource.metrics['job-parallelism']), 1)

        plugin._publish_measurement(1000)

        self.assertEqual(len(plugin.datasource.metrics['time-progress']), 2)
        self.assertEqual(len(plugin.datasource.metrics['job-progress']), 2)
        self.assertEqual(
            len(plugin.datasource.metrics['application-progress.error']), 2)
        self.assertEqual(len(plugin.datasource.metrics['job-parallelism']), 2)

    def test_wrong_request_body(self):
        """
        Asserts that a BadRequestException will occur
        if one of the parameters is missing
        Args: None
        Returns: None
        """

        request_error_counter = len(self.info_plugin)
        for key in self.info_plugin:
            info_plugin_test = self.info_plugin.copy()
            del info_plugin_test[key]
            try:
                KubeJobProgress(self.app_id, info_plugin_test,
                                self.collect_period, self.retries)
            except ex.BadRequestException:
                request_error_counter -= 1

        self.assertEqual(request_error_counter, 0)


if __name__ == "__main__":
    unittest.main()
