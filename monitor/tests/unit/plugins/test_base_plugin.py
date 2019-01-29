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

from monitor.plugins.base import Plugin


class TestPluginBase(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_init_empty_plugin(self):
        plugin_1 = Plugin(3)
        plugin_2 = Plugin(3)

        self.assertNotEqual(plugin_1, plugin_2)
        self.assertFalse(plugin_1.running)
        self.assertEqual(plugin_1.dimensions, {})
        self.assertEqual(plugin_1.collect_period, 3)
        self.assertEqual(plugin_1.attempts, 30)
        self.assertEqual(plugin_1.app_id, None)

        self.assertFalse(plugin_2.running)
        self.assertEqual(plugin_2.dimensions, {})
        self.assertEqual(plugin_2.collect_period, 3)
        self.assertEqual(plugin_2.attempts, 30)
        self.assertEqual(plugin_2.app_id, None)

    def test_stop_plugin(self):
        plugin = Plugin(3)

        plugin.running = True
        plugin.stop()
        self.assertFalse(plugin.running)


