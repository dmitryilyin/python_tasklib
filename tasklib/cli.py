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

import argparse
import sys
import os
import textwrap

import yaml

from tasklib import agent
from tasklib import config
from tasklib import exceptions
from tasklib import common
from contextlib import contextmanager


class CmdApi(object):
    """
    TaskLib CLI utility
    """

    def __init__(self):
        self.parser = argparse.ArgumentParser(
            description=textwrap.dedent(self.__doc__),
            formatter_class=argparse.RawDescriptionHelpFormatter)
        self.subparser = self.parser.add_subparsers(
            title='actions',
            description='Supported actions',
            help='Provide of one valid actions')
        self.config = config.Config()
        self.register_options()
        self.register_actions()

    def register_options(self):
        self.parser.add_argument(
            '--config', '-c', dest='config', default=None,
            help='Path to a configuration file')
        self.parser.add_argument(
            '--debug', '-d', dest='debug', action='store_true', default=None)

    def register_actions(self):
        task_arg = [(('task',), {'type': str})]
        self.register_parser('list')
        self.register_parser('conf')
        self.register_parser('log')
        self.register_parser('truncate')
        for name in ('run', 'daemon', 'report', 'status', 'show', 'clear'):
            self.register_parser(name, task_arg)

    def register_parser(self, func_name, arguments=()):
        parser = self.subparser.add_parser(func_name)
        parser.set_defaults(func=getattr(self, func_name))
        for args, kwargs in arguments:
            parser.add_argument(*args, **kwargs)

    def parse(self, args):
        parsed = self.parser.parse_args(args)
        if parsed.config:
            self.config.update_from_file(parsed.config)
        if parsed.debug is not None:
            self.config['debug'] = parsed.debug
        if parsed.config is None:
            local_log = 'tasklib.yaml'
            if os.path.isfile(local_log):
                parsed.config = local_log
        return parsed.func(parsed)

    def list(self, args):
        library = common.task_library(self.config)
        tasks = library.keys()
        tasks.sort()
        max_len = common.max_task_id_length(library)
        for task_id in tasks:
            if not isinstance(library[task_id], dict):
                continue
            task_type = common.task_type(library[task_id])
            if not task_type:
                continue
            actions = common.task_action_present(library[task_id])

            common.output(task_id, fill=max_len + 3, newline=False)
            common.output('(' + task_type + ')', fill=10, newline=False)
            common.output('[' + ', '.join(actions) + ']')

    def show(self, args):
        with self.rescue_exceptions():
            library = common.task_library(self.config)
            if not args.task in library:
                raise exceptions.NotFound()
            common.output(yaml.dump(
                library[args.task],
                default_flow_style=False
            ))

    def run(self, args):
        with self.rescue_exceptions():
            task_agent = agent.Agent(args.task, self.config)
            task_agent.run()
            status = task_agent.status()
            common.output("Task status: '%s'" % status)
            common.output("Report:")
            common.output(common.report_to_text(task_agent.report()))
            return task_agent.code()

    def daemon(self, args):
        with self.rescue_exceptions():
            task_agent = agent.Agent(args.task, self.config)
            task_agent.daemon()

    def report(self, args):
        with self.rescue_exceptions():
            task_agent = agent.Agent(args.task, self.config)
            common.output(common.report_to_text(task_agent.report()))

    def status(self, args):
        with self.rescue_exceptions():
            task_agent = agent.Agent(args.task, self.config)
            common.output("Task status: '%s'" % task_agent.status())
            return task_agent.code()

    def clear(self, args):
        with self.rescue_exceptions():
            task_agent = agent.Agent(args.task, self.config)
            task_agent.clear()

    def conf(self, args):
        common.output(self.config)

    def log(self, args):
        log_file = self.config['log_file']
        if log_file and os.path.isfile(log_file):
            command = "less +F --chop-long-lines '%s'" % log_file
            os.system(command)

    def truncate(self, args):
        log_file = self.config['log_file']
        if log_file and os.path.isfile(log_file):
            with open(log_file, 'w') as lf:
                lf.truncate()

    @contextmanager
    def rescue_exceptions(self):
        try:
            yield
        except exceptions.NotFound as e:
            common.output(e.msg)
            sys.exit(common.STATUS.not_found.code)
        except exceptions.AlreadyRunning as e:
            common.output(e.msg)
            sys.exit(common.STATUS.already_running.code)
        except exceptions.NotValidMetadata as e:
            common.output(e.msg)
            sys.exit(common.STATUS.error.code)

##############################################################################


def main():
    api = CmdApi()
    exit_code = api.parse(sys.argv[1:])
    exit(exit_code)
