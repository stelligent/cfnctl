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
import cfnctl.lib.stack_set as stack_set

# @pytest.mark.skip(reason='Long running - skip while testing locally')
@mock.patch('botocore.client.BaseClient._make_request')
def test_wait_for_stack_set(mock_api):
    '''
    pause execution until the stack creation is complete
    '''
    mock_api.side_effect = [
        MockResponse(
            200,
            {
                'Summaries': [
                    {
                        'Status': 'RUNNING',
                    },
                ],
            }
        ),
        MockResponse(
            200,
            {
                'Summaries': [
                    {
                        'Status': 'SUCCEEDED',
                    },
                ],
            }
        ),
    ]
    stack_set.wait_for_stack_set('foo')
    assert mock_api.call_count is 2

@mock.patch('botocore.client.BaseClient._make_request')
def test_stack_set_exists(mock_api):
    '''
    verify a stack exists
    '''
    mock_api.return_value = MockResponse(
        200,
        {
            'Summaries': [
                {
                    'StackSetName': 'foo',
                    'StackSetId': 'foo',
                    'Description': 'foo',
                    'Status': 'ACTIVE',
                },
            ]
        }
    )
    exists = stack_set.stack_set_exists('foo')
    assert mock_api.called
    assert exists == True

@mock.patch('botocore.client.BaseClient._make_request')
def test_stack_set_not_exists(mock_api):
    '''
    verify a stack exists
    '''
    mock_api.return_value = MockResponse(
        200,
        {
            'Summaries': [
                {
                    'StackSetName': 'bar',
                    'StackSetId': 'bar',
                    'Description': 'bar',
                    'Status': 'ACTIVE',
                },
            ]
        }
    )
    exists = stack_set.stack_set_exists('foo')
    assert mock_api.called
    assert exists == False
