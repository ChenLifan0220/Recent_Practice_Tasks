import os

from devops.MongoLogsTask.app.version import __version__
from packages.core.messercore.deployment import ECSTaskDeployment

env = {'USER': 'MONGO_USER', 'PROJECT': 'MONGO_PROJECT'}

server_region = os.getenv('SERVER_REGION')
env['SERVER'] = server_region

TASK_ROLE = 'ecsMesserMongoLogReportRole'
TASK_NAME = 'INT_MesserMongoLogReport'

if os.getenv('INSTALL'):
    task = ECSTaskDeployment(TASK_NAME)
    task.create_task_role(TASK_ROLE)
else:
    task = ECSTaskDeployment(TASK_NAME, role_name=TASK_ROLE)

task.add_container('mongo-log-report', image_name='mongo-log-report', image_label=__version__,
                   log_prefix='internal', environment_vars=env, namespace='internal')
task.create_definition()