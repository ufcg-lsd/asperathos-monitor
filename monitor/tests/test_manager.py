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
import mock
import unittest

from monitor.utils.monasca.connector import MonascaConnector


class TestManager(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass
        
    @unittest.skip
    @mock.patch('ConfigParser.RawConfigParser')
    @mock.patch('monitor.utils.monasca.connector.MonascaConnector._get_monasca_client')
    def test_init_manager(self, config_mock, monasca_mock):
        MonascaConnector()
        config_mock.assert_called_once_with()
        monasca_mock.assert_called_once_with()
    @unittest.skip
    @mock.patch('monitor.utils.monasca.connector.MonascaConnector._get_monasca_client')
    def test_get_measurements(self, monasca_mock):
        ConfigParser.RawConfigParser = mock.Mock()
        m = MonascaConnector()
        m.get_measurements(None, None)
        monasca_mock.assert_called_once_with()
