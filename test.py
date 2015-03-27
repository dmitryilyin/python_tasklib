from tasklib import config
from tasklib import agent
from tasklib import common


config = config.Config()
config['tasks_directory'] = '/home/dilyin/repos/tasklib/tasklib/tests/functional/exec/simple'
a = agent.Agent('test-simple', config)
a.run()
print a.status
print a.report