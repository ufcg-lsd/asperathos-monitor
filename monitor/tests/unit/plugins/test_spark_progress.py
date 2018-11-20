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

import mock
import time
import unittest

from monitor.plugins.spark_progress import SparkProgress

class TestPluginBase(unittest.TestCase):

    def setUp(self):
        self.info = {'spark_submisson_url': '0.0.0.0',
                     'expected_time': 400
                     }

    def tearDown(self):
        pass

    def test_init_empty_plugin(self):
        info1 = {'spark_submisson_url': '0.0.0.0',
                 'expected_time': 400
                 }

        info2 = {'spark_submisson_url': '0.0.0.0',
                 'expected_time': 400
                 }
        plugin_1 = SparkProgress("app-01", info1, 5)
        plugin_2 = SparkProgress("app-02", info2, 6)

        self.assertNotEqual(plugin_1, plugin_2)
        self.assertFalse(plugin_1.running)
        self.assertEqual(plugin_1.dimensions, {'application_id': 'app-01', 'service': 'spark-sahara'})
        self.assertEqual(plugin_1.collect_period, 5)
        self.assertEqual(plugin_1.attempts, 60)
        self.assertEqual(plugin_1.app_id, "app-01")

        self.assertFalse(plugin_2.running)
        self.assertEqual(plugin_2.dimensions, {'application_id': 'app-02', 'service': 'spark-sahara'})
        self.assertEqual(plugin_2.collect_period, 6)
        self.assertEqual(plugin_2.attempts, 60)
        self.assertEqual(plugin_2.app_id, 'app-02')

    def test_stop_plugin(self):
        plugin = SparkProgress("app-01", self.info, 5)

        plugin.running = True
        plugin.stop()
        self.assertFalse(plugin.running)

    def test_get_elapsed_time(self):
        timestamp = "2017-04-11T00:00:00.0003GMT"
        plugin = SparkProgress("app-01", self.info, 5)

        plugin._get_elapsed_time(timestamp)
        pass
