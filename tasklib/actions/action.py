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

# Action is responsible for the details of a specific task type, either
# the task itself or pre/post test.
#
# * Action SHOULD be created by a task and should be given the parent task an
#   the dictionary of values that will be used to determine what the action
#   should do
# * Action SHOULD verify that it has all the required data and the data
#   is correct by the 'verify' function and during the initialization.
# * If verification is failed action should raise 'exceptions.NotValidMetadata'
# * Action SHOULD run its payload when 'run' method is called.
# * If action is failed it should raise 'exceptions.Failed'
# * Action SHOULD return report when 'report' method is called. The report
#   should be a String, preferably in xUnit xml format, or None, it there is
#   no report to return.
# * Action MAY implement 'reset' method to reload to the initial state if it's
#   required.
# * Action MAY use logger and config values from the parent task.
# * Action MUST NOT work with reports and tests, it's Task's job.
# * Action MUST NOT interfere with status and processes, it's Agent's job.

from tasklib import exceptions


class Action(object):
    """
    Abstract action class
    It should be inherited and implemented by other actions
    """

    def __init__(self, task, data):
        self.task = task
        self.data = data
        self.verify()
        self.logger = task.logger
        self.logger.debug("Task: '%s' action: '%s' init",
                          self.task.name, self.type)

    @property
    def type(self):
        return self.__class__.__name__

    def reset(self):
        pass

    def verify(self):
        if not isinstance(self.data, dict):
            raise exceptions.NotValidMetadata()

    def run(self):
        raise NotImplementedError('Should be implemented by action driver.')

    def report(self):
        raise NotImplementedError('Should be implemented by action driver.')
