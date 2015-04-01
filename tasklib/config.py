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


class Config(object):

    def __init__(self, config_file=None):
        self.config = self.default_config
        if config_file and os.path.exists(config_file):
                self.update_from_file(config_file)

    @property
    def default_config(self):
        return {
            'tasks_directory': '/etc/puppet/modules/osnailyfacter/modular/',
            'tasks_pattern': '*tasks.yaml',
            'puppet_modules': '/etc/puppet/modules',
            'puppet_options': '--logdest syslog '
                              '--logdest /var/log/puppet.log '
                              '--logdest console '
                              '--trace '
                              '--evaltrace '
                              '--verbose '
                              '--debug '
                              '--report',
            'report_dir': '/var/tmp/task_report',
            'pid_dir': '/var/tmp/task_pid',
            'status_dir': '/var/tmp/task_status',
            'log_file': '/var/tmp/tasklib.log',
            'debug': False,
        }

    def update_from_file(self, config_file):
        if os.path.exists(config_file):
            with open(config_file) as f:
                loaded = yaml.load(f.read())
            self.config.update(loaded)

    def __getitem__(self, key):
        return self.config.get(key, None)

    def __setitem__(self, key, value):
        self.config[key] = value

    def __repr__(self):
        return yaml.dump(self.config, default_flow_style=False)
