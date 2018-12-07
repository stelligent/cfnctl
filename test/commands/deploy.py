import os
import unittest
import datetime
import boto3
import botocore
from test.mocks.s3 import S3
from test.mocks.cloudformation import Cloudformation
from botocore.stub import Stubber
from cfnctl.commands.deploy import _get_template_url, _upload_template, _wait_for_stack

class TestDeploy(unittest.TestCase):

    def test_template_url(self):
        local_url = _get_template_url('foo', 'baz', 'bar.template')
        file_url = _get_template_url('foo', 'baz', 'file:///test/bar.template')
        http_url = _get_template_url('foo', 'baz', 'https://www.templates.com/bar.template')
        self.assertEqual(local_url, 'https://s3.amazonaws.com/foo/baz/bar.template')
        self.assertEqual(file_url, 'https://s3.amazonaws.com/foo/baz/bar.template')
        self.assertEqual(http_url, 'https://www.templates.com/bar.template')
    
    def test_upload_template(self):
        '''upload a template with just a name
        '''
        def upload(file_path, bucket, template_name):
            self.assertEqual(template_name, 'baz/bar.template')
            self.assertEqual(bucket, 'foo')
            self.assertEqual(file_path, os.path.abspath('bar.template'))
            return
        client = S3()
        client.mock('upload_file', upload)
        _upload_template(client, 'baz', 'foo', 'bar.template')
        self.assertEqual(client.called['upload_file'], 1)
        self.assertEqual(True, True)

    def test_upload_template_url(self):
        '''should not attempt to upload a template that is already a url
        '''
        def upload(file_path, bucket, template_name):
            return
        client = S3()
        client.mock('upload_file', upload)
        _upload_template(client, 'baz', 'foo', 'http://templates.com/bar.template')
        self.assertEqual(client.called['upload_file'], 0)
    
    def test_upload_template_file_path(self):
        '''upload a template with just a name
        '''
        def upload(file_path, bucket, template_name):
            self.assertEqual(template_name, 'baz/bar.template')
            self.assertEqual(bucket, 'foo')
            self.assertEqual(file_path, os.path.abspath('file:///foo/bar.template'))
            return
        client = S3()
        client.mock('upload_file', upload)
        _upload_template(client, 'baz', 'foo', 'file:///foo/bar.template')
        self.assertEqual(client.called['upload_file'], 1)
        self.assertEqual(True, True)

    def test_wait_for_stack(self):
        def describe_stack_events(StackName, NextToken):
            # mock the call again
            if client.called['describe_stack_events'] == 3:
                return {'StackEvents': []}
            client.mock('describe_stack_events', describe_stack_events)
            return {
                'StackEvents': [
                    {
                        'LogicalResourceId': StackName,
                        'ResourceStatus': 'CREATE_IN_PROGRESS', 
                        'ResourceStatusReason': 'User Initiated', 
                        'StackName': StackName, 
                        'EventId': 1
                    }, 
                    {
                        'LogicalResourceId': StackName,
                        'ResourceStatus': 'REVIEW_IN_PROGRESS',
                        'ResourceStatusReason': 'User Initiated', 
                        'StackName': StackName,
                        'EventId': 2
                    }
                ]
            }
        
        def describe_stacks(StackName):
            client.mock('describe_stacks', describe_stacks)
            status = 'CREATE_IN_PROGRESS'
            if client.called['describe_stack_events'] == 3:
                status = 'CREATE_COMPLETE'
            return {
                'Stacks': [
                    {
                        'StackName': StackName,
                        'StackStatus': status
                    }
                ],
                'NextToken': 'string'
            }

        client = Cloudformation()
        client.mock('describe_stack_events', describe_stack_events)
        client.mock('describe_stacks', describe_stacks)
        # events = {u'StackEvents': [{u'StackId': 'arn:aws:cloudformation:us-west-2:324320755747:stack/cfnctl-test-bucket/a0016020-f9bd-11e8-a102-50a68a2012ba', u'EventId': 'a2246730-f9bd-11e8-94d9-0a9faee06ddc',u'ResourceStatus': 'CREATE_IN_PROGRESS', u'ResourceType': 'AWS::CloudFormation::Stack', u'Timestamp': datetime.datetime(2018, 12, 7, 1, 15, 49, 902000, tzinfo=tzutc()), u'ResourceStatusReason': 'User Initiated', u'StackName': 'cfnctl-test-bucket', u'PhysicalResourceId': 'arn:aws:cloudformation:us-west-2:324320755747:stack/cfnctl-test-bucket/a0016020-f9bd-11e8-a102-50a68a2012ba', u'LogicalResourceId': 'cfnctl-test-bucket'}, {u'StackId': 'arn:aws:cloudformation:us-west-2:324320755747:stack/cfnctl-test-bucket/a0016020-f9bd-11e8-a102-50a68a2012ba', u'EventId': 'a000eaf0-f9bd-11e8-a102-50a68a2012ba', u'ResourceStatus': 'REVIEW_IN_PROGRESS', u'ResourceType': 'AWS::CloudFormation::Stack', u'Timestamp': datetime.datetime(2018, 12, 7, 1, 15, 46, 543000, tzinfo=tzutc()), u'ResourceStatusReason': 'User Initiated', u'StackName': 'cfnctl-test-bucket', u'PhysicalResourceId': 'arn:aws:cloudformation:us-west-2:324320755747:stack/cfnctl-test-bucket/a0016020-f9bd-11e8-a102-50a68a2012ba', u'LogicalResourceId': 'cfnctl-test-bucket'}], 'ResponseMetadata': {'RetryAttempts': 0, 'HTTPStatusCode': 200, 'RequestId': 'a22af77a-f9bd-11e8-b16f-bf6d6bb0ef94', 'HTTPHeaders': {'x-amzn-requestid': 'a22af77a-f9bd-11e8-b16f-bf6d6bb0ef94', 'date': 'Fri, 07 Dec 2018 01:15:49 GMT', 'content-length': '1828', 'content-type': 'text/xml'}}}
        _wait_for_stack(client, 'foo')
        self.assertEqual(True, True)

if __name__ == '__main__':
    unittest.main()
