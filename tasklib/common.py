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

from collections import namedtuple
import fnmatch
import os
import subprocess
import yaml


Status = namedtuple('Status', ['name', 'code'])


def key_value_enum(enums):
    enums = dict([(k, Status(k, v)) for k, v in enums.iteritems()])
    return type('Enum', (), enums)

STATUS = key_value_enum({
    'success':     0,
    'run_pre':     1,
    'run_task':    2,
    'run_post':    3,
    'fail_pre':    4,
    'fail_task':   5,
    'fail_post':   6,
    'not_found':   7,
})


def task_library(config):
    library = {}
    for task_file in tasks_files(config):
        if not os.path.isfile(task_file):
            continue
        task_data = process_task_data(task_file)
        library.update(task_data)
    return library


def process_task_data(task_file):
    task_data = {}
    task_directory = os.path.dirname(task_file)
    with open(task_file, 'r') as tf:
        try:
            tasks = yaml.load(tf)
            if not isinstance(tasks, list):
                return task_data
            for task in tasks:
                if not 'id' in task:
                    continue
                if not 'type' in task:
                    continue
                if not task['type'] in ['puppet', 'shell']:
                    continue
                if 'parameters' in task:
                    if not 'cwd' in task:
                        task['parameters']['cwd'] = task_directory
                task_data[task['id']] = task
        except:
            return task_data
    return task_data


def tasks_files(config):
    for root, dirnames, filenames in os.walk(config['tasks_directory']):
        for filename in fnmatch.filter(filenames, config['tasks_pattern']):
            yield os.path.join(root, filename)


def ensure_dir_created(path):
    if not os.path.exists(path):
        os.makedirs(path)


def execute(cmd):
    command = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    stdout, stderr = command.communicate()
    return command.returncode, stdout, stderr
