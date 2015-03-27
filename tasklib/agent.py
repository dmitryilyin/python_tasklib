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

    def run(self):
        if not self.verify():
            return common.STATUS.not_found.code

        self.logger.debug("Task: '%s' agent run", self.task.name)
        self.task.reset()

        try:
            self.save_status(common.STATUS.run_pre.name)
            self.task.pre()
            self.save_report()
        except exceptions.Failed:
            self.logger.warning("Task: '%s' have failed the pre test!",
                                self.task.name)
            self.save_status(common.STATUS.fail_pre.name)
            return common.STATUS.fail_pre.code

        try:
            self.save_status(common.STATUS.run_task.name)
            self.task.run()
            self.save_report()
        except exceptions.Failed:
            self.logger.warning("Task: '%s' have failed!",
                                self.task.name)
            self.save_status(common.STATUS.fail_task.name)
            return common.STATUS.fail_task.code

        try:
            self.save_status(common.STATUS.run_post.name)
            self.task.post()
            self.save_report()
        except exceptions.Failed:
            self.logger.warning("Task: '%s' have failed the post test!",
                                self.task.name)
            self.save_status(common.STATUS.fail_post.name)
            return common.STATUS.fail_post.code

        self.save_status(common.STATUS.success.name)
        self.logger.debug("Task: '%s' agent end", self.task.name)
        return common.STATUS.success.code

    @property
    def report(self):
        if not os.path.exists(self.report_file):
            return None
        with open(self.report_file) as f:
            return f.read()

    @property
    def code(self):
        return getattr(common.STATUS, self.status).code

    @property
    def status(self):
        if not self.verify():
            return common.STATUS.not_found.name
        if not os.path.exists(self.status_file):
            return common.STATUS.not_found.name
        with open(self.status_file) as f:
            return f.read()

    @property
    def is_failed(self):
        return self.code

    def __repr__(self):
        return "TaskLib/Agent('%s')" % self.task.name

    def save_status(self, status):
        with open(self.status_file, 'w') as f:
            f.write(status)

    def save_report(self):
        with open(self.report_file, 'w') as f:
            f.write(yaml.dump(self.task.report))

    @property
    def pid_file(self):
        return os.path.join(self.config['pid_dir'],
                            self.task.name + '.pid')

    @property
    def status_file(self):
        return os.path.join(self.config['status_dir'],
                            self.task.name + '.status')

    @property
    def report_file(self):
        return os.path.join(self.config['report_dir'],
                            self.task.name + '.report')

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

    def clean(self):
        if os.path.exists(self.pid_file):
            os.unlink(self.pid_file)
        if os.path.exists(self.status_file):
            os.unlink(self.status_file)
        if os.path.exists(self.report_file):
            os.unlink(self.report_file)