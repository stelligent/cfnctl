#!/usr/bin/env python

#
# Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file
# except in compliance with the License. A copy of the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is distributed on an "AS IS"
# BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under the License.
#

'''
Control Cloudformation stack lifecycle
'''

import sys
import argparse
import logging
from . import commands

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)


def arg_deploy(parser, action):
    '''
    Deploy subcommand and arguments
    '''
    # command = parser.add_subparsers(description='command to run',
    #                                 dest='deploy')

    command_deploy = parser.add_parser(
        'deploy', help='creates a changeset and executes to create or update stack')
    required_group = command_deploy.add_argument_group('required arguments')
    required_group.add_argument(
        '-s', dest='stack_name', required=True, help="Stack name")
    required_group.add_argument(
        '-t', dest='template', required=True, help='CFN Template from local file or URL')
    optional_group = command_deploy.add_argument_group('optional arguments')
    optional_group.add_argument(
        '-b', dest='bucket', required=False, help='Bucket to upload template to')
    optional_group.add_argument(
        '-nr', dest='no_rollback', required=False, help='Do not rollback', action='store_true')
    optional_group.add_argument('-p', dest='parameters', required=False,
                                help='Local parameters JSON file', default='parameters.json')
    command_deploy.set_defaults(func=action)
    return parser

def arg_lambda(parser, action):
    '''
    Lambda subcommand and arguments
    '''
    # command = parser.add_subparsers(description='command to run',
    #                                 dest='lambda')

    command_lambda = parser.add_parser(
        'lambda', help='creates an archive and loads it to S3 to create a lambda from')
    required_group = command_lambda.add_argument_group('required arguments')
    required_group.add_argument(
        '-s', dest='source', required=True, help='Source folder to zip and upload')
    optional_group = command_lambda.add_argument_group('optional arguments')
    optional_group.add_argument(
        '-o', dest='output', required=False, help='Destination of the archive file')
    optional_group.add_argument(
        '-b', dest='bucket', required=False, help='Bucket to upload archive to')

    command_lambda.set_defaults(func=action)
    return parser

def arg_parser():
    '''
    Create an argparse object with global arguments and return
    '''
    parser = argparse.ArgumentParser(prog='cfnctl',
                                     description='Launch and manage CloudFormation stacks')
    parser.add_argument('-p', dest='aws_profile',
                        required=False, help='AWS Profile')
    parser.add_argument('-r', dest='region', required=False, help="Region name")

    if len(sys.argv) == 1:
        parser.print_help()
        parser.exit()

    return parser


def main():
    '''
    CFNCTL entrypoint
    '''
    parser = arg_parser()
    subparsers = parser.add_subparsers()
    arg_deploy(subparsers, commands.deploy)
    arg_lambda(subparsers, commands.lambda_command)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print '\nReceived Keyboard interrupt.'
        print 'Exiting...'
    except ValueError as error:
        print 'ERROR: {0}'.format(error)
