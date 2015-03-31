# Copyright 2014 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
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

# A task is responsible for choosing what action should be used for each
# supported task type as well as pre and post test types if these tests are
# present. A task should run tests if they are enabled and present and save
# report files.
#
# * A task SHOULD be created by an agent with the agent instance and task
#   metadata dictionary as parameters.
# * A task SHOULD verify itself and raise 'exceptions.NotValidMetadata'
#   if verification is failed when 'verify' is called and in __init__.
# * A task SHOULD run itself when 'test' method is called.
# * A task SHOULD run pre test if 'pre' method is called and pre test exists.
# * A task SHOULD run pre test if 'post' method is called and post test exists.
# * A task SHOULD run pre, task and post if 'run' method is called. Failed
#   action stops the run.
# * A task SHOULD collect reports from tests and actions and save them to the
#   report files.
# * A task SHOULD maintain the status file with its current status.
# * A task SHOULD return the current status and its code when
#   'status' and 'code' methods are called.
# * A task should return the reports of tests and actions when
#   the 'report' method is called with 'pre', 'task' and 'post' parameters
# * A task MUST NOT go into the details of how an action is working.
# * A task MUST NOT interfere with pid, status and other Agent's jobs.
#
# * Task's 'parameters' contains the actual job the task should do
# * Pre test is run before the task and, it it fails, task will not be started
#   at all. Pre test parameters are inside 'test_pre'.
# * Post test is run after the task and, it it fails, task is considered
#   unsuccessful even if the task itself did not fail. Post test parameters
#   are inside 'test_post'.
# * A task can have any set of pre, post and task parameters. A task without
#   any of them is valid too. It will successfully do nothing.
# * The action used for task or test is determined by the task type or test
#   type. These types should be present in the task or an action data.

import os
from tasklib.actions import shell
from tasklib.actions import puppet
from tasklib import common
from tasklib import exceptions
from contextlib import contextmanager

# use stevedore here
type_mapping = {
    'shell': shell.ShellAction,
    'exec': shell.ShellAction,
    'puppet': puppet.PuppetAction,
}


class Task(object):
    def __init__(self, agent, data):
        self.agent = agent
        self.config = agent.config
        self.logger = agent.logger
        self.data = data
        self._status = None
        self._report = {}
        self.saved_directory = None
        self.verify()
        self.known_actions = ['pre', 'task', 'post']
        self.logger.debug("Task: '%s' task init", self.id)

    ##

    @property
    def id(self):
        return self.data.get('id', None)

    @property
    def name(self):
        return self.id

    @property
    def type(self):
        if 'type' in self.parameters:
            return self.parameters['type']
        return self.data.get('type', None)

    @property
    def parameters(self):
        return self.data.get('parameters', {})

    @property
    def task_directory(self):
        return self.parameters.get('cwd', None)

    ##

    @property
    def task_data(self):
        return self.parameters

    @property
    def pre_data(self):
        return self.data.get('test_pre', None)

    @property
    def post_data(self):
        return self.data.get('test_post', None)

    ##

    @property
    def task_type(self):
        return self.type

    @property
    def pre_type(self):
        if 'cmd' in self.pre_data and not 'type' in self.pre_data:
            return 'shell'
        return self.pre_data.get('type', None)

    @property
    def post_type(self):
        if 'cmd' in self.post_data and not 'type' in self.post_data:
            return 'shell'
        return self.post_data.get('type', None)

    ##

    def __repr__(self):
        return "TaskLib/Task('%s')" % self.id

    def __str__(self):
        return self.__repr__()

    ##

    def report_file(self, action):
        # filter out unknown actions
        if not action in self.known_actions:
            self.logger.warning("Task: '%s' unknown report action: '%s'" %
                                (self.id, action))
            raise exceptions.NotValidMetadata()
        return os.path.join(self.config['report_dir'], self.id + '.' + action)

    def status_file(self):
        return os.path.join(self.config['status_dir'], self.id + '.status')

    ##

    def save_status(self, status):
        self._status = status
        #TODO set process title to Task(id) - status
        status_file = self.status_file()
        if status is None:
            self.remove_status_file()
            return
        with open(status_file, 'w') as f:
            f.write(status)

    def save_report(self, action, report):
        if report is None:
            if action in self._report:
                del self._report[action]
            self.remove_report_file(action)
        else:
            self._report[action] = report
            with open(self.report_file(action), 'w') as f:
                f.write(report)

    ##

    def remove_status_file(self):
        status_file = self.status_file()
        if not os.path.exists(status_file):
            return None
        os.unlink(status_file)

    def remove_report_file(self, action):
        report_file = self.report_file(action)
        if not os.path.exists(report_file):
            return None
        os.unlink(report_file)

    ##

    def report(self, action):
        # return report from memory if present
        if action in self._report:
            return self._report[action]

        # read report from file
        report_file = self.report_file(action)
        if not os.path.exists(report_file):
            return None
        with open(report_file, 'r') as f:
            return f.read()

    def code(self):
        return getattr(common.STATUS, self.status()).code

    def status(self):
        # return status from memory if present
        if self._status:
            return self._status

        # read status from file
        status_file = self.status_file()
        if not os.path.exists(status_file):
            return common.STATUS.not_found.name
        with open(status_file, 'r') as f:
            return f.read()

    ##

    def verify(self):
        if not self.id and self.type:
            raise exceptions.NotValidMetadata()

    def reset(self):
        self.save_status(None)
        for action in self.known_actions:
            self.save_report(action, None)

    def action(self, action_type, data):
        action_class = type_mapping.get(action_type)
        if action_class is None:
            raise exceptions.NotValidMetadata()
        action = action_class(self, data)
        return action

    @contextmanager
    def inside_task_directory(self):
        self.saved_directory = None
        if self.task_directory and os.path.isdir(self.task_directory):
            self.saved_directory = os.getcwd()
            os.chdir(self.task_directory)
        yield
        if self.saved_directory:
            os.chdir(self.saved_directory)

    ##

    def run(self):
        self.logger.debug("Task: '%s' run start", self.id)

        try:
            self.save_status(common.STATUS.run_pre.name)
            self.pre()
        except exceptions.Failed:
            self.logger.warning("Task: '%s' pre test failed!", self.id)
            self.save_status(common.STATUS.fail_pre.name)
            return common.STATUS.fail_pre.code

        try:
            self.save_status(common.STATUS.run_task.name)
            self.run()
        except exceptions.Failed:
            self.logger.warning("Task: '%s' task failed!", self.id)
            self.save_status(common.STATUS.fail_task.name)
            return common.STATUS.fail_task.code

        try:
            self.save_status(common.STATUS.run_post.name)
            self.post()
        except exceptions.Failed:
            self.logger.warning("Task: '%s' post test failed!", self.id)
            self.save_status(common.STATUS.fail_post.name)
            return common.STATUS.fail_post.code

        self.save_status(common.STATUS.success.name)
        self.logger.debug("Task: '%s' run end", self.id)
        return common.STATUS.success.code

    def task(self):
        if not self.task_data and self.task_type:
            return None
        action = self.action(self.type, self.task_data)
        with self.inside_task_directory():
            self.logger.debug("Task: '%s' start action: task", self.id)
            action.run()
            report = action.report()
            self.save_report('task', report)
            self.logger.debug("Task: '%s' end action: task", self.id)

    def pre(self):
        if not self.pre_data and self.pre_type:
            return None
        action = self.action(self.pre_type, self.pre_data)
        with self.inside_task_directory():
            self.logger.debug("Task: '%s' start action: pre", self.id)
            action.run()
            report = action.report()
            self.save_report('pre', report)
            self.logger.debug("Task: '%s' end action: pre", self.id)

    def post(self):
        if not self.post_data and self.pre_type:
            return None
        action = self.action(self.post_type, self.post_data)
        with self.inside_task_directory():
            self.logger.debug("Task: '%s' start action: post", self.id)
            action.run()
            report = action.report()
            self.save_report('post', report)
            self.logger.debug("Task: '%s' end action: post", self.id)