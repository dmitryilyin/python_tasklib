#    Copyright 2014 Mirantis, Inc.
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

import os
import yaml

from tasklib.actions import shell
from tasklib.actions import puppet
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
        self.saved_directory = None
        self.report = {}
        if not self.verify():
            raise exceptions.NotValidMetadata()

        self.logger.debug("Task: '%s' task init", self.id)

    def verify(self):
        if not self.id:
            return False
        if not self.type:
            return False
        return True

    def reset(self):
        self.report = {}

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

    @property
    def pre_data(self):
        return self.data.get('test_pre', None)

    @property
    def post_data(self):
        return self.data.get('test_post', None)

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

    def __repr__(self):
        return "TaskLib/Task('%s')" % self.id

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

    def run(self):
        action = self.action(self.type, self.parameters)
        with self.inside_task_directory():
            self.logger.debug("Task: '%s' start action: run", self.id)
            action.run()
            self.report['run'] = action.report()
            self.logger.debug("Task: '%s' end action: run", self.id)
        return self.report['run']

    def pre(self):
        if not self.pre_data:
            return None
        action = self.action(self.pre_type, self.pre_data)
        with self.inside_task_directory():
            self.logger.debug("Task: '%s' start action: pre", self.id)
            action.run()
            self.report['pre'] = action.report()
            self.logger.debug("Task: '%s' end action: pre", self.id)
        return self.report['pre']

    def post(self):
        if not self.post_data:
            return None
        action = self.action(self.post_type, self.post_data)
        with self.inside_task_directory():
            self.logger.debug("Task: '%s' start action: post", self.id)
            action.run()
            self.report['post'] = action.report()
            self.logger.debug("Task: '%s' end action: post", self.id)
        return self.report['post']