'''
Bucket operations
Make a bucket if it does not exist, convert paths to
s3 urls, and upload files to S3. Any logic required
around operating S3 belongs here.
'''

import os
import re
import logging

def is_url(search):
    '''
    Check if the string argument is a url
    '''
    return re.match('https?://', search) is not None

def s3_path(stack, template):
    '''
    Turn a stack name and template file into an S3 path
    '''
    return '{}/{}'.format(stack, os.path.basename(template))

def upload_file(stack, bucket, template_name):
    '''
    Upload the cfn template to S3
    '''
    logging.info('Uploading file %s', template_name)
    client = boto3.client('s3')
    if is_url(template_name):
        return None, template_name
    file_path = os.path.abspath(template_name)
    path = s3_path(stack, template_name)
    return client.upload_file(file_path, bucket, path), path

def get_file_url(bucket, stack, template_name):
    '''Get the cfn template url
    with the bucket name

    return string - template URL
    '''
    if is_url(template_name):
        return template_name
    return 'https://s3.amazonaws.com/{}/{}'.format(bucket, s3_path(stack, template_name))


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

def maybe_make_bucket(simple_storage_service, region, account_id):
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
        Bucket=stack_bucket
    )
    simple_storage_service.put_bucket_versioning(
        Bucket=stack_bucket,
        VersioningConfiguration={
            # 'MFADelete': 'Enabled', # requires MFA device added
            'Status': 'Enabled'
        },
    )
    return stack_bucket
