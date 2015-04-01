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

from tasklib.actions import action
from tasklib import exceptions
from tasklib import common


class ShellAction(action.Action):
    def __init__(self, task, data):
        self.code = None
        self.stdout = None
        self.stderr = None
        super(ShellAction, self).__init__(task, data)

    def verify(self):
        super(ShellAction, self).verify()
        if 'cmd' not in self.data:
            raise exceptions.NotValidMetadata()

    def reset(self):
        self.code = None
        self.stdout = None
        self.stderr = None

    @property
    def command(self):
        return self.data['cmd']

    def run(self):
        self.logger.debug("Task: '%s' action: '%s' run command: '%s'",
                          self.task.name, self.type, self.command)
        self.reset()
        self.code, self.stdout, self.stderr = common.execute(self.command)
        self.logger.debug("Task: '%s' action: '%s' %s" % (
            self.task.name,
            self.type,
            self.report(),
        ))
        if self.code != 0:
            raise exceptions.Failed(self.task.name, self.type)
        return self.code

    def report(self):
        if not self.stderr and self.stdout and self.code:
            return None
        return "command: '%s' stdout: '%s' stderr: '%s' code: '%s'" % (
            self.command,
            self.stdout,
            self.stderr,
            self.code,
        )
