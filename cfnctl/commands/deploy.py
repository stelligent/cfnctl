from jinja2 import Environment, FileSystemLoader
import boto3
import datetime
import time
import logging
import json
import os
import sys
import argparse


# email_prefix = 'rjulian'
# template_name = 'landing-zone.template'
# parameter_file = 'parameters.json'

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# if os.environ.get('GITHUB_TOKEN') == None:
#     logging.warn(' missing GITHUB_TOKEN enviornment variable')
#     quit()

def _upload_template(s3, bucket, template_name):
    '''Upload the cfn template
    to S3
    '''
    logging.info('Uploading template file')
    s3.upload_file('./{}'.format(template_name), bucket, template_name)


def _bucket_exists(s3, name):
    '''Check if a bucket exists
    by name

    return bool
    '''
    logging.info('Verifying S3 bucket exists')
    buckets = s3.list_buckets()
    exists = False
    for bucket in buckets['Buckets']:
        if bucket['Name'] == name:
            exists = True
            break
    return exists


def _maybe_make_bucket(s3, region, account_id):
    '''Make a bucket to upload
    the cfn template to if
    it does not exist

    return string - bucket name
    '''
    logging.info('Maybe make S3 bucket')
    stack_bucket = 'landing-zone-template-bucket-{}-{}'.format(
        region, account_id)
    if _bucket_exists(s3, stack_bucket) == True:
        logging.info('Bucket exists')
        return stack_bucket

    logging.info('No S3 bucket found, creating {}'.format(stack_bucket))
    s3.create_bucket(Bucket=stack_bucket)
    s3.put_bucket_versioning(
        Bucket=stack_bucket,
        VersioningConfiguration={
            'MFADelete': 'Enabled',
            'Status': 'Enabled'
        }
    )
    return stack_bucket

def _stack_exists(client, name):
    '''Check if a cfn stack exists
    by name

    return bool
    '''
    logging.info('Verifying Stack exists')
    stacks = client.describe_stacks(StackName=name)
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
    setName = stack + datetime.datetime.now().strftime('%y-%m-%d-%H%M%S')
    logging.info('Stack exists: {}'.format(exists))
    logging.info('template url: {}'.format(template))
    client.create_change_set(
        StackName=stack,
        TemplateURL=template,
        UsePreviousTemplate=False,
        Parameters=parameters,
        Capabilities=[
            'CAPABILITY_NAMED_IAM',
        ],
        ChangeSetName=setName,
        ChangeSetType='UPDATE' if exists else 'CREATE'
    )
    return setName


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
        return True

    if description['Status'] == 'FAILED':
        logging.error('Error: Failed to create change set')
        return False

    logging.info('Waiting for change set creation. Status: {}'.format(description['Status']))
    time.sleep(3)
    return _wait_for_changeset(client, changeset, stack)


def _execute_changeset(client, changeset, stack):
    '''Execute a created changeset

    return client.execute_change_set
    '''
    logging.info('Executing changeset')
    return client.execute_change_set(
        ChangeSetName=changeset,
        StackName=stack
    )


def _get_parameters():
    '''Get parameters for a cfn template

    return object
    '''
    logging.info('Getting template parameters')
    return '{}'
    # templateEnv = Environment(
    #     loader=FileSystemLoader(searchpath="./")
    # )
    # template = templateEnv.get_template(parameter_file)
    # logging.info('Rendering parameter jinja2 template')
    # rendered = template.render(
    #     email=email_prefix,
    #     github_token=os.environ.get('GITHUB_TOKEN')
    # )
    # return json.loads(rendered)


def _get_template_url(bucket, template_name):
    '''Get the cfn template url
    with the bucket name

    return string - template URL
    '''
    return 'https://s3.amazonaws.com/{}/{}'.format(bucket, template_name)


def deploy(args):
  logging.info('Calling deploy')
  stack = args.stack_name
  client = boto3.client('cloudformation')
  s3 = boto3.client('s3')
  account_id = boto3.client('sts').get_caller_identity().get('Account')
  region = args.region or boto3.session.Session().region_name
  bucket = _maybe_make_bucket(s3, region, account_id)
  # TODO: normalize template name
  _upload_template(s3, bucket, args.template)
  changeset = _make_change_set(client, stack, _get_template_url(bucket, 'test'), _get_parameters())
  ready = _wait_for_changeset(client, changeset, stack)
  if ready == False:
      return

  _execute_changeset(client, changeset, stack)


# deploy()