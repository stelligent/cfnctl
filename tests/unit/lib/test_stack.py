'''
Test stack operations
'''
import pytest
from unittest import mock
import datetime
from unittest.mock import ANY
from tests.unit.mocks.mock import (
    MockResponse,
    mock_wait_for_stack,
    mock_change_set,
    boto_client_error
)
import cfnctl.lib.stack as stack

# @pytest.mark.skip(reason='Long running - skip while testing locally')
@mock.patch('botocore.client.BaseClient._make_request')
def test_wait_for_stack(mock_api):
    '''
    pause execution until the stack creation is complete
    '''
    mock_api.side_effect = mock_wait_for_stack(2, 'foo')
    stack.wait_for_stack('foo')
    assert mock_api.call_count is 4

@mock.patch('botocore.client.BaseClient._make_request')
def test_stack_exists(mock_api):
    '''
    verify a stack exists
    '''
    mock_api.return_value = MockResponse(
        200,
        {
            'Stacks': [
                {
                    'StackName': 'foo',
                    'StackStatus': 'CREATE_COMPLETE'
                }
            ],
            'NextToken': 'string'
        },
    )
    exists = stack.stack_exists('foo')
    assert mock_api.called
    assert exists == True

@mock.patch('botocore.client.BaseClient._make_request')
def test_stack_exists_false(mock_api):
    '''
    verify a stack exists
    '''
    mock_api.side_effect = boto_client_error(
        'InvalidRequestException',
        'describe_stacks',
        'not exist'
    )
    exists = stack.stack_exists('foo')
    assert mock_api.called
    assert exists == False

@mock.patch('botocore.client.BaseClient._make_request')
def test_stack_not_exists(mock_api):
    '''verify a stack exists
    '''
    mock_api.return_value = MockResponse(
        200,
        {
            'Stacks': [
                {
                    'StackName': 'bar',
                    'StackStatus': 'CREATE_COMPLETE'
                }
            ],
            'NextToken': 'string'
        },
    )
    exists = stack.stack_exists('foo')
    assert mock_api.called
    assert exists == False

@mock.patch('botocore.client.BaseClient._make_request')
def test_make_create_change_set(mock_api):
    '''create a changeset
    '''
    stack_name = 'foo'
    mock_api.side_effect = [
        # mock stack exists
        MockResponse(
            200,
            {
                'Stacks': [
                    {
                        'StackName': 'bar',
                        'StackStatus': 'CREATE_COMPLETE'
                    }
                ],
                'NextToken': 'string'
            },
        ),
        # mock create changeset response
        MockResponse(
            200,
            {
                'Id': 'string',
                'StackId': 'string'
            }
        ),
    ]
    stack.make_change_set(stack_name, 'https://s3.amazon.com/foobar/test.template', [])
    assert mock_api.called
    # verify the parameters sent to make a changeset
    mock_api.assert_called_with(
        ANY,
        {
            'url_path': ANY,
            'query_string': ANY,
            'method': ANY,
            'headers': ANY,
            'body': {
                'Action': 'CreateChangeSet',
                'Version': ANY,
                'StackName': ANY,
                'TemplateURL': ANY,
                'UsePreviousTemplate': ANY,
                'Parameters': ANY,
                'Capabilities.member.1': ANY,
                'ChangeSetName': ANY,
                'ChangeSetType': 'CREATE'
            },
            'url': ANY,
            'context': ANY
        },
        ANY
    )

@mock.patch('botocore.client.BaseClient._make_request')
def test_make_update_change_set(mock_api):
    '''update a stack with changeset
    '''
    stack_name = 'foo'
    mock_api.side_effect = [
        # mock stack exists
        MockResponse(
            200,
            {
                'Stacks': [
                    {
                        'StackName': stack_name,
                        'StackStatus': 'CREATE_COMPLETE'
                    }
                ],
                'NextToken': 'string'
            },
        ),
        # mock create changeset response
        MockResponse(
            200,
            {
                'Id': 'string',
                'StackId': 'string'
            }
        ),
    ]
    stack.make_change_set(stack_name, 'https://s3.amazon.com/foobar/test.template', [])
    assert mock_api.called
    # verify the parameters sent to make a changeset
    mock_api.assert_called_with(
        ANY,
        {
            'url_path': ANY,
            'query_string': ANY,
            'method': ANY,
            'headers': ANY,
            'body': {
                'Action': 'CreateChangeSet',
                'Version': ANY,
                'StackName': ANY,
                'TemplateURL': ANY,
                'UsePreviousTemplate': ANY,
                'Parameters': ANY,
                'Capabilities.member.1': ANY,
                'ChangeSetName': ANY,
                'ChangeSetType': 'UPDATE'
            },
            'url': ANY,
            'context': ANY
        },
        ANY
    )

# @pytest.mark.skip(reason='Long running - skip while testing locally')
@mock.patch('botocore.client.BaseClient._make_request')
def test_wait_for_changeset(mock_api):
    '''
    pause execution until the changeset creation is complete
    '''
    mock_api.side_effect = mock_change_set(3, 'foo')

    finished = stack.wait_for_changeset('foo', 'bar')
    assert mock_api.call_count is 3
    assert finished == True

# @pytest.mark.skip(reason='Long running - skip while testing locally')
@mock.patch('botocore.client.BaseClient._make_request')
def test_wait_for_changeset_failed(mock_api):
    '''
    pause execution until the changeset creation is complete
    '''
    mock_api.side_effect = mock_change_set(3, 'foo', 'FAILED')

    finished = stack.wait_for_changeset('foo', 'bar')
    assert mock_api.call_count is 3
    assert finished == False

@mock.patch('botocore.client.BaseClient._make_request')
def test_stack_complete(mock_api):
    '''
    Check if the stack status is in a complete state
    '''
    mock_api.side_effect = [
        MockResponse(
            200,
            {
                'Stacks': [
                    {
                        'StackName': 'foo',
                        'StackStatus': 'CREATE_COMPLETE'
                    }
                ],
                'NextToken': 'string'
            },
        )
    ]
    stack_status = stack.stack_complete('foo')
    assert mock_api.call_count is 1
    assert stack_status['complete'] == True

    mock_api.reset_mock()

    mock_api.side_effect = [
        MockResponse(
            200,
            {
                'Stacks': [
                    {
                        'StackName': 'foo',
                        'StackStatus': 'UPDATE_ROLLBACK_FAILED'
                    }
                ],
                'NextToken': 'string'
            },
        )
    ]
    stack_status = stack.stack_complete('foo')
    assert mock_api.call_count is 1
    assert stack_status['complete'] == True

@mock.patch('botocore.client.BaseClient._make_request')
def test_execute_changeset(mock_api):
    '''
    Check that execute changeset gets called
    '''
    mock_api.side_effect = [
        MockResponse(
            200,
            None,
        )
    ]
    stack.execute_changeset('foo', 'bar')
    assert mock_api.called

@mock.patch('botocore.client.BaseClient._make_request')
def test_get_parameters_empty(mock_api):
    # Need to check rendering a template. Loading a template from disk
    # and rendering should be separated. This is a placeholder
    parameters = stack.get_parameters(None)
    assert parameters == []

    parameters = stack.get_parameters('tests/unit/templates/parameters.json')
    assert parameters[0]['ParameterKey'] == 'foo'
