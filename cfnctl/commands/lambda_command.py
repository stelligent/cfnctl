'''
Deploy subcommand logic
Handles creating an S3 bucket (if required) and uploading
template to the bucket
Creates and executes a changeset to either create a new
stack or update an existing stack
'''
import logging
import os
import zipfile
import boto3
import cfnctl.lib.bucket as bucket

def write_zip(path, ziph):
    '''
    Write files to a zip file
    path {string} absolute path to directory to zip
    ziph {ZipFile} ZipFile handle
    '''
    basedir = os.path.dirname(path)
    for root, _, files in os.walk(path):
        for filename in files:
            abspath = os.path.join(root, filename)
            ziph.write(abspath, abspath.replace(basedir, ''))

def zip_dir(path, name):
    '''
    Zip a directory
    path {string} absolute path to directory to zip
    name {string} absolute path to archive directory location/name
    '''
    if not name.endswith('.zip'):
        name = ''.join([name, '.zip'])
    logging.info('writing contents of %s to archive %s', path, name)
    zipf = zipfile.ZipFile(name, 'w', zipfile.ZIP_DEFLATED)
    write_zip(path, zipf)
    zipf.close()

def lambda_command(args):
    '''Deploy a lambda function
    '''
    logging.info('Calling lambda_command')
    simple_storage_service = boto3.client('s3')
    account_id = boto3.client('sts').get_caller_identity().get('Account')
    region = args.region or boto3.session.Session().region_name
    bucket_name = args.bucket or bucket.maybe_make_bucket(
        simple_storage_service,
        region,
        account_id
    )
    outfile = os.path.abspath(args.output or ''.join([args.source, '.zip']))
    source = os.path.abspath(args.source)
    zip_dir(source, outfile)
    bucket.upload_file(simple_storage_service, 'lambda', bucket_name, outfile)
    logging.info('Finished uploading archive')
    file_url = bucket.get_file_url(bucket_name, 'lambda', os.path.basename(outfile))
    logging.info(file_url)
