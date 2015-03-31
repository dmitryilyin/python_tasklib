# Copyright 2014 Mirantis, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import os
import daemonize

from tasklib import exceptions
from tasklib import task
from tasklib import common
from tasklib import logger
import yaml


class Agent(object):
    def __init__(self, task_name, config):
        self.config = config
        self.logger = logger.setup_logging(self.config, 'tasklib')
        self.logger.debug("Task: '%s' agent init", task_name)
        self.task = None
        self.pre = None
        self.post = None
        self.library = common.task_library(self.config)
        self.init_directories()

        if not task_name in self.library:
            self.logger.warning("Task: '%s' not found!", task_name)
            self.task = None
        else:
            task_data = self.library[task_name]
            self.task = task.Task(self, task_data)

    def init_directories(self):
        common.ensure_dir_created(self.config['pid_dir'])
        common.ensure_dir_created(self.config['report_dir'])
        common.ensure_dir_created(self.config['status_dir'])

    def verify(self):
        return self.task is not None

    def __repr__(self):
        return "TaskLib/Agent('%s')" % self.task.name

    @property
    def pid_file(self):
        return os.path.join(self.config['pid_dir'],
                            self.task.name + '.pid')

    def daemon(self):
        self.logger.debug("Task: '%s' daemonize with pid file: '%s'",
                          self.task.name, self.pid_file)
        daemon = daemonize.Daemonize(
            app=str(self),
            pid=self.pid_file,
            action=self.run,
        )
        daemon.start()
        return daemon

    def clean_pid(self):
        if os.path.exists(self.pid_file):
            os.unlink(self.pid_file)