'''
Deploy subcommand logic
Handles creating an S3 bucket (if required) and uploading
template to the bucket
Creates and executes a changeset to either create a new
stack or update an existing stack
'''
import logging
from typing import List
import boto3
import cfnctl.lib.stack as stack
import cfnctl.lib.stack_set as stack_set
import cfnctl.lib.bucket

def deploy_stack_set(stack_name: str, template: str, parameters: List[dict], accounts = List[str]) -> None:

    account_id = boto3.client('sts').get_caller_identity().get('Account')
    region = boto3.session.Session().region_name
    bucket = cfnctl.lib.bucket.maybe_make_bucket(region, account_id)
    cfnctl.lib.bucket.upload_file(stack_name, bucket, template)

    # Create or update the stack set
    stack_set.deploy_stack_set(
        stack_name=stack_name,
        template=cfnctl.lib.bucket.get_file_url(bucket, stack_name, template),
        parameters=parameters
    )
    stack_set.wait_for_stack_set(stack=stack_name)

    # Deploy the stacks to the accounts
    stack_set.deploy_stacks(stack=stack_name, accounts=accounts)

def deploy_stack(stack_name: str, template: str, parameters: str):
    changeset = stack.make_change_set(
        stack=stack_name,
        template=template,
        parameters=parameters,
    )
    ready = stack.wait_for_changeset(changeset, stack_name)
    if ready is False:
        return

    stack.execute_changeset(changeset, stack_name)
    stack.wait_for_stack(stack_name)

def deploy(args: object):
    '''
    Deploy a cloudformation stack
    '''
    logging.info('Calling deploy')

    account_id = boto3.client('sts').get_caller_identity().get('Account')

    stack_name = args.stack_name
    region = args.region or boto3.session.Session().region_name
    bucket = args.bucket or cfnctl.lib.bucket.maybe_make_bucket(region, account_id)
    accounts = args.accounts or ''
    template = cfnctl.lib.bucket.get_file_url(bucket, stack, args.template)
    parameters = stack.get_parameters(args.parameters)

    # Upload the template file to our bucket
    cfnctl.lib.bucket.upload_file(stack, bucket, args.template)

    if args.stack_set:
        return deploy_stack_set(
            stack_name=stack_name,
            template=template,
            parameters=parameters,
            accounts=str(accounts).split(','),
        )

    deploy_stack(
        stack_name=stack_name,
        template=template,
        parameters=parameters,
    )

