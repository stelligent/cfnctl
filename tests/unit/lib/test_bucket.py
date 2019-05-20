'''
Test bucket lib functionality
'''
import os
from unittest import mock
from tests.unit.mocks.mock import MockResponse
import cfnctl.lib.bucket as bucket

def test_template_url():
    '''
    verify the generated url matches what we expect
    '''
    local_url = bucket.get_file_url('foo', 'baz', 'bar.template')
    file_url = bucket.get_file_url('foo', 'baz', 'file:///test/bar.template')
    http_url = bucket.get_file_url('foo', 'baz', 'https://www.templates.com/bar.template')

    assert local_url == 'https://s3.amazonaws.com/foo/baz/bar.template'
    assert local_url == 'https://s3.amazonaws.com/foo/baz/bar.template'
    assert file_url == 'https://s3.amazonaws.com/foo/baz/bar.template'
    assert http_url == 'https://www.templates.com/bar.template'

@mock.patch('botocore.client.BaseClient._make_request')
def test_upload_template(mock_api):
    '''
    upload a template with just a name
    '''
    mock_api.return_value = MockResponse(
        200,
        None,
    )
    _, path = bucket.upload_file('baz', 'foo', 'tests/unit/templates/bar.template')
    assert path == 'baz/bar.template'
    assert mock_api.call_count is 1

@mock.patch('botocore.client.BaseClient._make_request')
def test_upload_template_url(mock_api):
    '''
    should not attempt to upload a template that is already a url
    '''
    mock_api.return_value = MockResponse(
        200,
        None,
    )
    _, path = bucket.upload_file('baz', 'foo', 'http://templates.com/bar.template')
    assert path == 'baz/bar.template'
    assert mock_api.call_count is 0

@mock.patch('boto3.s3.transfer.S3Transfer.upload_file')
def test_upload_template_file_path(mock_api):
    '''
    upload a template with just a name
    '''
    mock_api.return_value = MockResponse(
        200,
        None,
    )
    UNIT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    bucket.upload_file('baz', 'foo', 'tests/unit/templates/bar.template')
    mock_api.assert_called_with(
        bucket='foo',
        callback=None,
        extra_args=None,
        filename=f'{UNIT_DIR}/templates/bar.template',
        key='baz/bar.template'
    )

def test_is_url():
    '''
    check if a string is a url
    '''
    assert bucket.is_url('test.com') == False
    assert bucket.is_url('htt://test.com') == False

    assert bucket.is_url('http://test.com') == True
    assert bucket.is_url('https://test.co') == True
    assert bucket.is_url('https://test') == True

def test_s3_path():
    assert bucket.s3_path('foo', 'bar') == 'foo/bar'
    assert bucket.s3_path('foo', 'baz/bar') == 'foo/bar'
    assert bucket.s3_path('foo', 'file:///baz/bar.template') == 'foo/bar.template'
    assert bucket.s3_path('foo', 'bar.json') == 'foo/bar.json'
    assert bucket.s3_path('foo', 'bar.yaml') == 'foo/bar.yaml'
    assert bucket.s3_path('baz/foo', 'bar.yaml') == 'baz/foo/bar.yaml'
    assert bucket.s3_path('baz/foo', 'bar.yaml') == 'baz/foo/bar.yaml'

@mock.patch('botocore.client.BaseClient._make_request')
def test_bucket_exists(mock_api):
    mock_api.return_value = MockResponse(
        200,
        {'Buckets': [
            {
                'Name': 'foo'
            }
        ]},
    )
    exists = bucket.bucket_exists('foo')
    assert mock_api.call_count is 1
    assert exists == True

    mock_api.reset_mock()
    mock_api.return_value = MockResponse(
        200,
        {'Buckets': [
            {
                'Name': 'bar'
            }
        ]},
    )
    exists = bucket.bucket_exists('foo')
    assert mock_api.call_count is 1
    assert exists == False

@mock.patch('botocore.client.BaseClient._make_request')
def test_maybe_make_bucket_false(mock_api):
    '''
    Test calling make bucket if the bucket already exists
    '''
    mock_api.side_effect = [
        MockResponse(
            200,
            {'Buckets': [
                {
                    'Name': 'cfnctl-staging-bucket-us-east-1-00000000000'
                }
            ]},
        ),
    ]
    bucket_name = bucket.maybe_make_bucket('us-east-1', '00000000000')
    assert mock_api.call_count is 1
    assert bucket_name == 'cfnctl-staging-bucket-us-east-1-00000000000'

@mock.patch('botocore.client.BaseClient._make_request')
def test_maybe_make_bucket_true(mock_api):
    '''
    Test actually making the bucket
    '''
    mock_api.side_effect = [
        MockResponse(
            200,
            {'Buckets': [
                {
                    'Name': 'foobar'
                }
            ]},
        ),
        MockResponse(
            200,
            {
                'Location': 'string'
            },
        ),
        MockResponse(
            200,
            None,
        ),
    ]
    bucket_name = bucket.maybe_make_bucket('us-east-1', '00000000001')
    assert mock_api.call_count is 3
    assert bucket_name == 'cfnctl-staging-bucket-us-east-1-00000000001'
