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
import sys


Status = namedtuple('Status', ['name', 'code'])


def key_value_enum(enums):
    enums = dict([(k, Status(k, v)) for k, v in enums.iteritems()])
    return type('Enum', (), enums)

STATUS = key_value_enum({
    'success':         0,
    'run_pre':         1,
    'run_task':        2,
    'run_post':        3,
    'fail_pre':        4,
    'fail_task':       5,
    'fail_post':       6,
    'not_found':       7,
    'already_running': 8,
    'error':           9,
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


def output(string, newline=True, fill=None):
    string = str(string)
    if fill:
        string = string[0:fill].ljust(fill)
    if newline and not string.endswith("\n"):
        string += "\n"
    sys.stdout.write(string)


def max_task_id_length(library):
    tasks = library.keys()
    if len(tasks) == 0:
        return None
    return len(max(tasks, key=len))


def report_to_text(report):
    if not isinstance(report, dict):
        return
    text_report = ''
    for action in ['pre', 'task', 'post']:
        if not action in report:
            continue
        text_report += "===== %s =====\n" % action
        report_data = report[action]
        if not report_data.endswith("\n"):
            report_data += "\n"
        text_report += report_data
    return text_report


def task_type(task_data):
    parameters_type = task_data.get('parameters', {}).get('type', None)
    if parameters_type:
        return parameters_type
    if 'type' in task_data:
        return task_data['type']
    return None


def task_action_present(task_data):
    actions = []
    if 'test_pre' in task_data:
        actions.append('pre')
    if 'parameters' in task_data:
        actions.append('task')
    if 'test_post' in task_data:
        actions.append('post')
    return actions