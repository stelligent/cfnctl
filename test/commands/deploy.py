import os
import unittest
import boto3
import botocore
from test.mocks.s3 import S3
from botocore.stub import Stubber
from cfnctl.commands.deploy import _get_template_url, _upload_template

class TestDeploy(unittest.TestCase):

    def test_template_url(self):
        local_url = _get_template_url('foo', 'bar.template')
        file_url = _get_template_url('foo', 'file:///test/bar.template')
        http_url = _get_template_url('foo', 'https://www.templates.com/bar.template')
        self.assertEqual(local_url, 'https://s3.amazonaws.com/foo/bar.template')
        self.assertEqual(file_url, 'https://s3.amazonaws.com/foo/bar.template')
        self.assertEqual(http_url, 'https://www.templates.com/bar.template')
    
    def test_upload_template(self):
        '''upload a template with just a name
        '''
        def upload(template_name, bucket, file_path):
            self.assertEqual(template_name, 'bar.template')
            self.assertEqual(bucket, 'foo')
            self.assertEqual(file_path, os.path.abspath('bar.template'))
            return
        client = S3()
        client.mock('upload_file', upload)
        _upload_template(client, 'foo', 'bar.template')
        self.assertEqual(client.called['upload_file'], 1)
        self.assertEqual(True, True)

    def test_upload_template_url(self):
        '''should not attempt to upload a template that is already a url
        '''
        def upload(template_name, bucket, file_path):
            return
        client = S3()
        client.mock('upload_file', upload)
        _upload_template(client, 'foo', 'http://templates.com/bar.template')
        self.assertEqual(client.called['upload_file'], 0)
    
    def test_upload_template_file_path(self):
        '''upload a template with just a name
        '''
        def upload(template_name, bucket, file_path):
            self.assertEqual(template_name, 'bar.template')
            self.assertEqual(bucket, 'foo')
            self.assertEqual(file_path, '/foo/bar.template')
            return
        client = S3()
        client.mock('upload_file', upload)
        _upload_template(client, 'foo', 'file:///foo/bar.template')
        self.assertEqual(client.called['upload_file'], 1)
        self.assertEqual(True, True)

if __name__ == '__main__':
    unittest.main()
