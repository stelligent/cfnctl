'''
Deploy subcommand logic
Handles creating an S3 bucket (if required) and uploading
template to the bucket
Creates and executes a changeset to either create a new
stack or update an existing stack
'''
import datetime
import time
import logging
import json
import os
import re
import sys
import boto3
import botocore.exceptions
from jinja2 import Environment, FileSystemLoader

def _upload_template(simple_storage_service, stack, bucket, template_name):
    '''Upload the cfn template
    to S3
    '''
    logging.info('Uploading template file')
    if _is_url(template_name):
        return None
    file_path = os.path.abspath(template_name)
    s3_path = _s3_path(stack, template_name)
    return simple_storage_service.upload_file(file_path, bucket, s3_path)


def _bucket_exists(simple_storage_service, name):
    '''Check if a bucket exists
    by name

    return bool
    '''
    logging.info('Verifying S3 bucket exists')
    buckets = simple_storage_service.list_buckets()
    exists = False
    for bucket in buckets['Buckets']:
        if bucket['Name'] == name:
            exists = True
            break
    return exists


def _maybe_make_bucket(simple_storage_service, region, account_id):
    '''Make a bucket to upload
    the cfn template to if
    it does not exist

    return string - bucket name
    '''
    logging.info('Maybe make S3 bucket')
    stack_bucket = 'cfnctl-staging-bucket-{}-{}'.format(
        region, account_id)
    if _bucket_exists(simple_storage_service, stack_bucket):
        logging.info('Bucket exists')
        return stack_bucket

    logging.info('No S3 bucket found, creating %s', stack_bucket)
    simple_storage_service.create_bucket(
        Bucket=stack_bucket,
        CreateBucketConfiguration={
            'LocationConstraint': region
        })
    simple_storage_service.put_bucket_versioning(
        Bucket=stack_bucket,
        VersioningConfiguration={
            'MFADelete': 'Enabled',
            'Status': 'Enabled'
        },
    )
    return stack_bucket


def _stack_exists(client, name):
    '''Check if a cfn stack exists
    by name

    return bool
    '''
    logging.info('Verifying Stack exists')
    stacks = None
    try:
        stacks = client.describe_stacks(StackName=name)
    except botocore.exceptions.ClientError as error:
        message = error.response.get('Error', {}).get('Message', 'Unknown')
        if 'not exist' in message:
            return False
        print error

    if not stacks:
        sys.exit()

    exists = False
    for stack in stacks['Stacks']:
        if stack['StackName'] == name:
            exists = True
            break
    return exists


def _make_change_set(client, stack, template, parameters):
    '''Create a change set for
    a cfn stack

    return client.create_change_set
    '''
    logging.info('Creating change set')
    exists = _stack_exists(client, stack)
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


def _wait_for_changeset(client, changeset, stack):
    '''Block script execution until a change
    set creates or fails

    return bool
    '''
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
        logging.error(description['StatusReason'])
        return False

    logging.info('Waiting for change set creation. Status: %s', description['Status'])
    time.sleep(3)
    return _wait_for_changeset(client, changeset, stack)

def _stack_complete(client, name):
    '''Check if a stack is in a complete (finished, failure)
    state
    '''
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


def _wait_for_stack(client, stack, token=None, old_events=None):
    '''Block script execution until the stack status
    is in a finished state

    return bool
    '''
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
    stack_status = _stack_complete(client, stack)
    if stack_status['complete']:
        logging.info('Stack finished in %s state', stack_status['status'])
        return None
    # make a list of previous stack events
    last_events = list([event['EventId'] for event in events['StackEvents']])
    return _wait_for_stack(
        client,
        stack,
        'NextToken' in events and events['NextToken'],
        last_events
    )


def _execute_changeset(client, changeset, stack):
    '''Execute a created changeset

    return client.execute_change_set
    '''
    logging.info('Executing changeset')
    return client.execute_change_set(
        ChangeSetName=changeset,
        StackName=stack
    )


def _get_parameters(parameter_file):
    '''Get parameters for a cfn template

    return object
    '''
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

def _is_url(search):
    return re.match('https?://', search) is not None

def _s3_path(stack, template):
    return '{}/{}'.format(stack, os.path.basename(template))

def _get_template_url(bucket, stack, template_name):
    '''Get the cfn template url
    with the bucket name

    return string - template URL
    '''
    if _is_url(template_name):
        return template_name
    return 'https://s3.amazonaws.com/{}/{}'.format(bucket, _s3_path(stack, template_name))


def deploy(args):
    '''Deploy a cloudformation stack
    '''
    logging.info('Calling deploy')
    stack = args.stack_name
    client = boto3.client('cloudformation')
    simple_storage_service = boto3.client('s3')
    account_id = boto3.client('sts').get_caller_identity().get('Account')
    region = args.region or boto3.session.Session().region_name
    bucket = args.bucket or _maybe_make_bucket(simple_storage_service, region, account_id)
    _upload_template(simple_storage_service, stack, bucket, args.template)
    changeset = _make_change_set(
        client,
        stack,
        _get_template_url(bucket, stack, args.template),
        _get_parameters(args.parameters)
    )
    ready = _wait_for_changeset(client, changeset, stack)
    if ready is False:
        return

    _execute_changeset(client, changeset, stack)
    _wait_for_stack(client, stack)
