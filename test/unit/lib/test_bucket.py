import os
from unittest import mock
import pytest
import datetime
from test.mocks.s3 import S3
from test.mocks.cloudformation import Cloudformation
import cfnctl.lib.bucket as bucket

def test_template_url(self):
    '''verify the generated url matches what we expect
    '''
    local_url = bucket.get_file_url('foo', 'baz', 'bar.template')
    file_url = bucket.get_file_url('foo', 'baz', 'file:///test/bar.template')
    http_url = bucket.get_file_url('foo', 'baz', 'https://www.templates.com/bar.template')
    self.assertEqual(local_url, 'https://s3.amazonaws.com/foo/baz/bar.template')
    self.assertEqual(file_url, 'https://s3.amazonaws.com/foo/baz/bar.template')
    self.assertEqual(http_url, 'https://www.templates.com/bar.template')

@mock.patch('botocore.client.BaseClient._make_request')
def test_upload_template(mock_api):
    '''upload a template with just a name
    '''
    def upload(file_path, bucket, template_name):
        self.assertEqual(template_name, 'baz/bar.template')
        self.assertEqual(bucket, 'foo')
        self.assertEqual(file_path, os.path.abspath('bar.template'))
        return
    client = S3()
    client.mock('upload_file', upload)


    mock_api.return_value = MockResponse(
        200,
        {
            'principals': [
                'arn:aws:iot:region:account_id:cert/foobar',
                'arn:aws:iot:region:account_id:cert/baz',
            ],
        },
    )
    cert = get_certificate(thing='my-test-core')
    assert cert == [
        'arn:aws:iot:region:account_id:cert/foobar',
        'arn:aws:iot:region:account_id:cert/baz',
    ]


    bucket.upload_file('baz', 'foo', 'bar.template')
    self.assertEqual(client.called['upload_file'], 1)
    self.assertEqual(True, True)

# def test_upload_template_url(self):
#     '''should not attempt to upload a template that is already a url
#     '''
#     def upload(file_path, bucket, template_name):
#         return
#     client = S3()
#     client.mock('upload_file', upload)
#     bucket.upload_file(client, 'baz', 'foo', 'http://templates.com/bar.template')
#     self.assertEqual(client.called['upload_file'], 0)

# def test_upload_template_file_path(self):
#     '''upload a template with just a name
#     '''
#     def upload(file_path, bucket, template_name):
#         self.assertEqual(template_name, 'baz/bar.template')
#         self.assertEqual(bucket, 'foo')
#         self.assertEqual(file_path, os.path.abspath('file:///foo/bar.template'))
#         return
#     client = S3()
#     client.mock('upload_file', upload)
#     bucket.upload_file(client, 'baz', 'foo', 'file:///foo/bar.template')
#     self.assertEqual(client.called['upload_file'], 1)

# def test_is_url(self):
#     '''check if a string is a url
#     '''
#     self.assertEqual(bucket.is_url('test.com'), False)
#     self.assertEqual(bucket.is_url('htt://test.com'), False)

#     self.assertEqual(bucket.is_url('http://test.com'), True)
#     self.assertEqual(bucket.is_url('https://test.co'), True)
#     self.assertEqual(bucket.is_url('https://test'), True)

# def test_s3_path(self):
#     self.assertEqual(bucket.s3_path('foo', 'bar'), 'foo/bar')
#     self.assertEqual(bucket.s3_path('foo', 'baz/bar'), 'foo/bar')
#     self.assertEqual(bucket.s3_path('foo', 'file:///baz/bar.template'), 'foo/bar.template')
#     self.assertEqual(bucket.s3_path('foo', 'bar.json'), 'foo/bar.json')
#     self.assertEqual(bucket.s3_path('foo', 'bar.yaml'), 'foo/bar.yaml')
#     self.assertEqual(bucket.s3_path('baz/foo', 'bar.yaml'), 'baz/foo/bar.yaml')
#     self.assertEqual(bucket.s3_path('baz/foo', 'bar.yaml'), 'baz/foo/bar.yaml')

# def test_bucket_exists(self):
#     client = S3()
#     def list_buckets():
#         return {'Buckets': [
#             {
#                 'Name': 'foo'
#             }
#         ]}
#     client.mock('list_buckets', list_buckets)
#     exists = bucket._bucket_exists(client, 'foo')
#     self.assertEqual(exists, True)

#     client = S3()
#     def list_buckets2():
#         return {'Buckets': [
#             {
#                 'Name': 'bar'
#             }
#         ]}
#     client.mock('list_buckets', list_buckets2)
#     exists = bucket._bucket_exists(client, 'foo')
#     self.assertEqual(exists, False)

# def test_maybe_make_bucket(self):
#     # maybe_make_bucket(simple_storage_service, region, account_id)
#     self.assertEqual(True, True)
