# Copyright (c) 2017 LSD - UFCG.
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

import logging
from datetime import datetime


global_enabled = False


class Log:
    def __init__(self, name, output_file_path):
        self.logger = logging.getLogger(name)
        if not len(self.logger.handlers):
            handler = logging.StreamHandler()
            handler.setLevel(logging.INFO)
            self.logger.addHandler(handler)
            handler = logging.FileHandler(output_file_path)
            self.logger.addHandler(handler)
            self.logger.propagate = False

    def log(self, text):
        if global_enabled:
            self.logger.info(text)


class ScalingLog:
    def __init__(self, name, output_file_path, application_id=""):
        self.application_id = application_id
        self.logger = Log(name, output_file_path)

    def log(self, text):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
        log_string = "%s|%s|%s" % (self.application_id, timestamp, text)
        self.logger.log(log_string)


def enable():
    global global_enabled
    global_enabled = True


def disable():
    global global_enabled
    global_enabled = False


def configure_logging(logging_level="INFO"):
    levels = {"CRITICAL": logging.CRITICAL, "DEBUG": logging.DEBUG,
              "ERROR": logging.ERROR, "FATAL": logging.FATAL,
              "INFO": logging.INFO, "NOTSET": logging.NOTSET,
              "WARN": logging.WARN, "WARNING": logging.WARNING
              }

    logging.basicConfig(level=levels[logging_level])
