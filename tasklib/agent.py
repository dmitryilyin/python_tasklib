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

from tasklib import task
from tasklib import common
from tasklib import logger
from tasklib import exceptions


class Agent(object):
    def __init__(self, task_name, config):
        self.config = config
        self.logger = logger.setup_logging(self.config, 'tasklib')
        self.logger.debug("Task: '%s' agent init", task_name)
        self.task = None
        self.saved_directory = None
        self.init_task_name = task_name
        self.library = common.task_library(self.config)
        self.init_directories()

        if task_name in self.library:
            task_data = self.library[task_name]
            self.task = task.Task(self, task_data)

        self.verify()

    def init_directories(self):
        common.ensure_dir_created(self.config['pid_dir'])
        common.ensure_dir_created(self.config['report_dir'])
        common.ensure_dir_created(self.config['status_dir'])

    def verify(self):
        if self.task is None:
            raise exceptions.NotFound(
                self.init_task_name,
                self.config['tasks_directory']
            )

    def run(self):
        self.logger.debug('run start')
        try:
            if self.saved_directory and os.path.isdir(self.saved_directory):
                os.chdir(self.saved_directory)
            #self.logger.debug(self.task)
            if not self.task:
                return
            self.logger.debug('task!')
            self.task.logger = self.logger
            #self.logger.debug(os.getcwd())
            #self.logger.debug(self.cwd)
            self.task.run()
        except Exception as e:
            self.logger.debug(str(e))
        self.logger.debug('run end')
        # if self.running():
        #     raise exceptions.AlreadyRunning(self.task.name, self.pid)
        #return self.task.run()

    def status(self):
        if not self.task:
            return
        return self.task.status()

    def code(self):
        if not self.task:
            return
        return self.task.code()

    def report(self):
        if not self.task:
            return
        report = {}
        for action in ['pre', 'task', 'post']:
            if self.task.report(action):
                report[action] = self.task.report(action)
        return report

    def __repr__(self):
        return "Agent('%s')" % self.task.name

    def __str__(self):
        return self.__repr__()

    @property
    def pid_file(self):
        return os.path.join(self.config['pid_dir'],
                            self.task.name + '.pid')

    @property
    def pid(self):
        if not os.path.exists(self.pid_file):
            return None
        with open(self.pid_file, 'r') as f:
            return f.read()

    def running(self):
        if not self.pid:
            return False
        return self.pid_exists(self.pid)

    @staticmethod
    def pid_exists(pid):
        cmdline = '/proc/%s/cmdline' % pid
        return os.path.isdir(cmdline)

    def daemon(self):
        import logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False
        fh = logging.FileHandler("/tmp/test.log", "w")
        fh.setLevel(logging.DEBUG)
        self.logger.addHandler(fh)
        keep_fds = [fh.stream.fileno()]
        self.logger.debug("Task: '%s' daemonize with pid file: '%s'",
                          self.task.name, self.pid_file)
        self.saved_directory = os.getcwd()
        daemon = daemonize.Daemonize(
            app='tasklib',
            pid=self.pid_file,
            action=self.run,
            keep_fds=keep_fds,
        )
        daemon.start()
        return daemon

    def clear(self):
        if os.path.exists(self.pid_file):
            os.unlink(self.pid_file)
        if self.task:
            self.task.reset()