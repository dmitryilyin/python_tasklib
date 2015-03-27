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

from tasklib import exceptions


class Action(object):

    def __init__(self, task, data):
        self.task = task
        self.data = data
        self.logger = task.logger
        self.logger.debug("Task: '%s' action: '%s' init",
                          self.task.name, self.type)

    @property
    def type(self):
        return self.__class__.__name__

    def verify(self):
        if not isinstance(self.data, dict):
            raise exceptions.NotValidMetadata()

    def run(self):
        raise NotImplementedError('Should be implemented by action driver.')

    def report(self):
        raise NotImplementedError('Should be implemented by action driver.')
