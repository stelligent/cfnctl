import sys
import time
from typing import List
import cfnctl
import boto3

def create_stack_set(stack_name: str, template: str, parameters: List[dict], role: str = None) -> dict:
    '''
    Create a new stack set

    Args:
        stack_name (str): AWS Stack name
        template (str): S3 url for the template
        parameters list: [
            {
            "ParameterKey": "",
            "ParameterValue": ""
            }
        ]
    Returns:
        dict: {
            'StackSetId': 'string'
        }
    '''
    role = role or 'AWSCloudFormationStackSetAdministrationRole'
    client = boto3.client('cloudformation')
    return client.create_stack_set(
        StackSetName=stack_name,
        Description='Codepipeline cross account roles',
        TemplateURL=template,
        Parameters=parameters,
        Capabilities=[
            'CAPABILITY_NAMED_IAM',
        ],
        ExecutionRoleName=role,
    )

def update_stack_set(stack_name: str, template: str, parameters: List[dict], role: str = None):
    '''
    Update an existing stack set

    Args:
        stack_name (str): AWS Stack name
        template (str): S3 url for the template
        parameters list: [
            {
            "ParameterKey": "",
            "ParameterValue": ""
            }
        ]
    Returns:
        dict: {
            'OperationId': 'string'
        }
    '''
    role = role or 'AWSCloudFormationStackSetAdministrationRole'
    client = boto3.client('cloudformation')
    return client.update_stack_set(
        StackSetName=stack_name,
        TemplateURL=template,
        Parameters=parameters,
        Capabilities=[
            'CAPABILITY_NAMED_IAM',
        ],
        ExecutionRoleName=role,
    )

def wait_for_stack_set(stack, token=None):
    '''
    Wait for a stack sets operations to finish

    Args:
        client (object): Boto3 cloudformation client
        stack (str): AWS Stack name
    Returns:
        None
    '''
    client = boto3.client('cloudformation')
    describe = None
    if token is not None:
        describe = client.list_stack_set_operations(
            StackSetName=stack,
            NextToken=token
        )
    else:
        describe = client.list_stack_set_operations(
            StackSetName=stack
        )
    for operations in describe['Summaries']:
        if 'RUNNING' in operations['Status']:
            time.sleep(3)
            return wait_for_stack_set(stack)

    if 'NextToken' in describe:
        wait_for_stack_set(stack, describe['NextToken'])

    return None

def stack_set_exists(stack, token=None):
    '''
    Check if a stack set exists or not

    Args:
        client (object): Boto3 cloudformation client
        stack (str): AWS Stack name
        token (str): Paging token for the list_stack_sets api call
    Returns:
        bool
    '''
    client = boto3.client('cloudformation')
    response = None
    if token is not None:
        response = client.list_stack_sets(
            NextToken=token,
        )
    else:
        response = client.list_stack_sets()

    for stack_set in response['Summaries']:
        if stack_set['StackSetName'] == stack:
            return True

    if 'NextToken' in response:
        return stack_set_exists(stack, token)

    return False


def deploy_stack_set(stack_name: str, template: str, parameters: List[dict], role: str = None):
    '''
    Create or Update a stack set and return when it's complete

    Args:
        client (object): Boto3 cloudformation client
        stack (str): AWS Stack name
        template (str): S3 url for the template
        parameters list: [
            {
            "ParameterKey": "",
            "ParameterValue": ""
            }
        ]
    Returns:
        None
    '''
    if stack_set_exists(stack_name):
        update_stack_set(
            stack_name=stack_name,
            template=template,
            parameters=parameters,
            role=role,
        )
    else:
        create_stack_set(
            stack_name=stack_name,
            template=template,
            parameters=parameters,
            role=role,
        )

def create_instances(stack, accounts):
    '''
    Create instances in a stack set

    Args:
        client (object): Boto3 cloudformation client
        stack (str): AWS Stack name
    Returns:
        None
    '''
    client = boto3.client('cloudformation')
    client.create_stack_instances(
        StackSetName=stack,
        Accounts=accounts,
        Regions=[
            'us-east-1',
        ],
    )

def update_instances(stack, accounts):
    '''
    Update instances of a stack set

    Args:
        client (object): Boto3 cloudformation client
        stack (str): AWS Stack name
    Returns:
        None
    '''
    client = boto3.client('cloudformation')
    client.update_stack_instances(
        StackSetName=stack,
        Accounts=accounts,
        Regions=[
            'us-east-1',
        ],
    )

def need_create_stack_instances(stack, accounts):
    '''
    Checks if stack instances should be created

    Args:
        stack (str): AWS Stack name
        accounts (list[str]): List of account ids
    Returns:
        list: [
            string,
        ]
    '''
    client = boto3.client('cloudformation')
    launched = accounts[:]
    response = client.list_stack_instances(
        StackSetName=stack
    )
    for stack_set in response['Summaries']:
        if stack_set['Account'] in launched:
            launched.remove(stack_set['Account'])

    return launched

def deploy_stacks(stack, accounts):
    '''
    Create or update stacks in a stack set

    Args:
        client (object): Boto3 cloudformation client
        stack (str): AWS Stack name
    Returns:
        None
    '''
    if need_create_stack_instances(stack, accounts):
        return create_instances(stack=stack, accounts=accounts)
    return update_instances(stack=stack, accounts=accounts)
