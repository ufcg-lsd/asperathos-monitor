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

from datetime import datetime
from monitor.utils.job_report.job_report import JobReport


class TestKubeJobs(unittest.TestCase):

    def setUp(self):
        """
        Set up the JobReport instance
        Returns: None
        """

        info_plugin = {'scaling_strategy': 'pid',
                       'heuristic_options': {'proportional_gain': 0.1,
                                             'derivative_gain': 0,
                                             'integral_gain': 0
                                             }
                       }

        self.job_report = JobReport(info_plugin)

    def tearDown(self):
        pass

    def test_get_heuristic_options(self):

        heuristic_options = {'proportional_gain': 0.1,
                             'derivative_gain': 0,
                             'integral_gain': 0
                             }
        self.assertEqual(self.job_report.get_heuristic_options(),
                         heuristic_options)

    def test_verify_set_get_max_error(self):

        max_now = str(datetime.now())
        max_error = 0.175
        self.job_report.verify_and_set_max_error(max_error, max_now)
        self.assertEqual((max_error, max_now), self.job_report.get_max_error())

        now = str(datetime.now())
        max_error = 1
        self.job_report.verify_and_set_max_error(max_error, max_now)
        self.assertEqual((max_error, max_now), self.job_report.get_max_error())

        now = str(datetime.now())
        error = 0.5
        self.job_report.verify_and_set_max_error(error, now)
        self.assertEqual((max_error, max_now), self.job_report.get_max_error())

    def test_verify_set_get_mix_error(self):

        min_now = str(datetime.now())
        min_error = 0.175
        self.job_report.verify_and_set_min_error(min_error, min_now)
        self.assertEqual((min_error, min_now), self.job_report.get_min_error())

        min_now = str(datetime.now())
        min_error = 0.075
        self.job_report.verify_and_set_min_error(min_error, min_now)
        self.assertEqual((min_error, min_now), self.job_report.get_min_error())

        now = str(datetime.now())
        error = 2
        self.job_report.verify_and_set_min_error(error, now)
        self.assertEqual((min_error, min_now), self.job_report.get_min_error())

    def test_set_get_final_replicas(self):

        replicas = 10
        self.job_report.set_final_replicas(replicas)
        self.assertEqual(replicas, self.job_report.get_final_replicas())

    def test_set_get_final_error(self):

        error = 0.175
        now = str(datetime.now())
        self.job_report.set_final_error(error, now)
        self.assertEqual((error, now), self.job_report.get_final_error())

    def test_to_dict(self):

        scaling_strategy = 'pid'
        heuristic_options = {'proportional_gain': 0.1,
                             'derivative_gain': 0,
                             'integral_gain': 0
                             }

        max_now = str(datetime.now())
        max_error = 0.175
        self.job_report.verify_and_set_max_error(max_error, max_now)

        min_now = str(datetime.now())
        min_error = 0.105
        self.job_report.verify_and_set_min_error(min_error, min_now)

        final_replicas = 10
        self.job_report.set_final_replicas(final_replicas)

        error = 0.155
        now = str(datetime.now())
        self.job_report.set_final_error(error, now)

        to_dict = self.job_report.to_dict()

        self.assertEqual(to_dict['scaling_strategy'], scaling_strategy)
        self.assertEqual(to_dict['heuristic_options'], heuristic_options)
        self.assertEqual(to_dict['max_error'], (max_error, max_now))
        self.assertEqual(to_dict['min_error'], (min_error, min_now))
        self.assertEqual(to_dict['final_replicas'], final_replicas)
        self.assertEqual(to_dict['final_error'], (error, now))
