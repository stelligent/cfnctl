import datetime
import time
import logging
import json
import os
import sys
import boto3
import botocore.exceptions
from jinja2 import Environment, FileSystemLoader
import cfnctl.lib as lib

def _stack_exists(name):
    '''Check if a cfn stack exists
    by name

    return bool
    '''
    logging.info('Verifying Stack exists')
    client = boto3.client('cloudformation')
    stacks = None
    try:
        stacks = client.describe_stacks(StackName=name)
    except botocore.exceptions.ClientError as error:
        message = error.response.get('Error', {}).get('Message', 'Unknown')
        if 'not exist' in message:
            return False
        print(error)

    if not stacks:
        sys.exit()

    exists = False
    for stack in stacks['Stacks']:
        if stack['StackName'] == name:
            exists = True
            break
    return exists


def _make_change_set(stack, template, parameters):
    '''Create a change set for
    a cfn stack

    return client.create_change_set
    '''
    logging.info('Creating change set')
    client = boto3.client('cloudformation')
    exists = _stack_exists(stack)
    set_name = stack + datetime.datetime.now().strftime('%y-%m-%d-%H%M%S')
    logging.info('Stack exists: %s', exists)
    logging.info('template url: %s', template)
    client.create_change_set(
        StackName=stack,
        TemplateURL=template,
        UsePreviousTemplate=False,
        Parameters=parameters,
        Capabilities=[
            'CAPABILITY_NAMED_IAM',
        ],
        ChangeSetName=set_name,
        ChangeSetType='UPDATE' if exists else 'CREATE'
    )
    return set_name


def _wait_for_changeset(changeset, stack):
    '''Block script execution until a change
    set creates or fails

    return bool
    '''
    client = boto3.client('cloudformation')
    description = client.describe_change_set(
        ChangeSetName=changeset,
        StackName=stack
    )
    # CREATE_PENDING'|'CREATE_IN_PROGRESS'|'CREATE_COMPLETE'|'DELETE_COMPLETE'|'FAILED',
    if description['Status'] == 'CREATE_COMPLETE':
        logging.info('Waiting for change set creation. Status: %s', description['Status'])
        return True

    if description['Status'] == 'FAILED':
        logging.error('Error: Failed to create change set')
        logging.error(description['Status'])
        return False

    logging.info('Waiting for change set creation. Status: %s', description['Status'])
    time.sleep(3)
    return _wait_for_changeset(changeset, stack)

def _stack_complete(name):
    '''Check if a stack is in a complete (finished, failure)
    state
    '''
    client = boto3.client('cloudformation')
    stacks = client.describe_stacks(StackName=name)
    stack = stacks['Stacks'][0]
    complete_states = [
        'CREATE_FAILED',
        'CREATE_COMPLETE',
        'ROLLBACK_COMPLETE',
        'DELETE_FAILED',
        'DELETE_COMPLETE',
        'UPDATE_COMPLETE',
        'UPDATE_ROLLBACK_FAILED',
        'UPDATE_ROLLBACK_COMPLETE'
    ]
    return {
        'complete': stack['StackStatus'] in complete_states,
        'status': stack['StackStatus']
    }


def _wait_for_stack(stack, token=None, old_events=None):
    '''Block script execution until the stack status
    is in a finished state

    return bool
    '''
    client = boto3.client('cloudformation')
    events = None
    if token:
        events = client.describe_stack_events(
            StackName=stack,
            NextToken=token
        )
    else:
        events = client.describe_stack_events(
            StackName=stack
        )
    if not old_events:
        old_events = []
    # determine which events are new
    new_events = list(
        [event for event in events['StackEvents'] if event['EventId'] not in old_events]
    )
    # log new events
    for _, event in enumerate(new_events):
        logging.info(
            '%s %s %s',
            event['LogicalResourceId'],
            event['ResourceStatus'],
            'ResourceStatusReason' in event and event['ResourceStatusReason'] or ''
        )
    # wait a bit before doing this again
    time.sleep(3)
    # if the stack is complete we'll stop (we should query one more time for events probably)
    stack_status = _stack_complete(stack)
    if stack_status['complete']:
        logging.info('Stack finished in %s state', stack_status['status'])
        return None
    # make a list of previous stack events
    last_events = list([event['EventId'] for event in events['StackEvents']])
    return _wait_for_stack(
        stack,
        'NextToken' in events and events['NextToken'],
        last_events
    )


def _execute_changeset(changeset, stack):
    '''Execute a created changeset

    return client.execute_change_set
    '''
    logging.info('Executing changeset')
    client = boto3.client('cloudformation')
    return client.execute_change_set(
        ChangeSetName=changeset,
        StackName=stack
    )


def _get_parameters(parameter_file):
    '''Get parameters for a cfn template

    return object
    '''
    if parameter_file is None:
        return []
    logging.info('Getting template parameters')
    logging.info(os.getcwd())
    template_env = Environment(
        loader=FileSystemLoader(searchpath=os.getcwd())
    )
    template = template_env.get_template(parameter_file)
    logging.info('Rendering parameter template')
    rendered = template.render(
        # email=email_prefix,
        # github_token=os.environ.get('GITHUB_TOKEN')
    )
    return json.loads(rendered)

