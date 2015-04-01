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


class TaskLibException(Exception):
    def __init__(self):
        self.msg = 'TaskLib abstract error!'


class NotFound(TaskLibException):
    def __init__(self, task_name, tasks_directory):
        self.task_name = task_name
        self.task_directory = tasks_directory
        self.msg = "Task: '%s' not found in '%s'!" % \
                   (self.task_name, self.task_directory)


class NotValidMetadata(TaskLibException):
    def __init__(self, object_name):
        self.object_name = object_name
        self.msg = "%s: missing critical items in metadata!" % \
                   self.object_name


class Failed(TaskLibException):
    def __init__(self, task_name, action_type):
        self.task_name = task_name
        self.action_type = action_type
        self.msg = "Task: '%s' action: '%s' have failed!" % \
                   (self.task_name, self.action_type)


class AlreadyRunning(TaskLibException):
    def __init__(self, task_name, pid):
        self.task_name = task_name
        self.pid = pid
        self.msg = "Task: '%s' is already running at pid: '%s'!" % \
                   (self.task_name, self.pid)
